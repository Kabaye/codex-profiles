"""Validate the public assembly manifest and read only explicitly selected sources."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def relative_path(value: object) -> str:
    if (not isinstance(value, str) or not value or any(char in value for char in '\\:<>|?*')
            or any(ord(char) < 32 for char in value)
            or PurePosixPath(value).is_absolute()
            or any(part in {"", ".", ".."} or part.endswith((".", " ")) for part in value.split("/"))):
        raise ValueError(f"Unsafe manifest source path: {value!r}")
    return value


def source_path(root: Path, value: str) -> Path:
    name = relative_path(value)
    base = root.resolve()
    path = root.joinpath(*PurePosixPath(name).parts)
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError(f"Linked manifest source requires manual review: {part}")
        if part == root:
            break
    if not path.resolve().is_relative_to(base):
        raise ValueError(f"Manifest source escapes the repository: {value}")
    return path


def source_bytes(root: Path, value: str) -> bytes:
    path = source_path(root, value)
    if not path.is_file():
        raise ValueError(f"Manifest source is not a regular file: {value}")
    return path.read_bytes().replace(b"\r\n", b"\n")


def source_text(root: Path, value: str) -> str:
    return source_bytes(root, value).decode("utf-8").replace("\r", "\n")


def load(root: Path = ROOT) -> dict:
    data = json.loads(source_text(root, "manifest.json"))
    if (not isinstance(data, dict) or type(data.get("schema_version")) is not int
            or data["schema_version"] != 1
            or set(data) != {"schema_version", "markers", "profiles", "opencode_agents", "roles_directory"}):
        raise ValueError("Unknown assembly manifest schema")
    role_dir = relative_path(data["roles_directory"])
    if not re.fullmatch(r"agents/[a-z][a-z0-9-]*", role_dir):
        raise ValueError("Role directory must be a named folder under agents/")
    markers = data.get("markers")
    if (not isinstance(markers, dict) or set(markers) != {"begin", "end"}
            or any(not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value
                   for value in markers.values()) or markers["begin"] == markers["end"]):
        raise ValueError("Assembly manifest requires distinct single-line markers")
    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("Assembly manifest requires profile recipes")

    def sources(value: object, suffix: str) -> None:
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise ValueError("Recipe sources must be ordered path lists")
        if len(value) != len(set(value)):
            raise ValueError("Duplicate source in assembly recipe")
        for name in value:
            relative_path(name)
            if PurePosixPath(name).suffix != suffix:
                raise ValueError(f"Unexpected recipe source type: {name}")

    for profile, modes in profiles.items():
        if not isinstance(profile, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", profile):
            raise ValueError("Invalid profile name in assembly manifest")
        if not isinstance(modes, dict) or not modes:
            raise ValueError(f"Profile has no mode recipes: {profile}")
        for mode, recipe in modes.items():
            if not isinstance(mode, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", mode):
                raise ValueError("Invalid mode name in assembly manifest")
            if not isinstance(recipe, dict) or set(recipe) != {"config", "roles", "instructions"}:
                raise ValueError("Recipe requires config, roles and instructions")
            sources(recipe["config"], ".toml")
            sources(recipe["roles"], ".toml")
            filenames = [PurePosixPath(name).name for name in recipe["roles"]]
            if len(filenames) != len(set(filenames)):
                raise ValueError("Duplicate role destination in assembly recipe")
            instructions = recipe["instructions"]
            if not isinstance(instructions, dict) or not instructions:
                raise ValueError("Recipe requires instruction destinations")
            for name, parts in instructions.items():
                relative_path(name)
                if "/" in name or PurePosixPath(name).suffix != ".md":
                    raise ValueError(f"Unsafe instruction destination: {name}")
                sources(parts, ".md")
                if not parts:
                    raise ValueError(f"Instruction destination has no sources: {name}")
    relative_path(data.get("opencode_agents"))
    return data


def recipe(data: dict, profile: str, mode: str | None = None) -> tuple[str, dict]:
    if profile not in data["profiles"]:
        raise ValueError(f"Unknown profile: {profile}")
    modes = data["profiles"][profile]
    selected = mode if mode is not None else next(iter(modes))
    if selected not in modes:
        raise ValueError(f"Unknown mode for {profile}: {selected}")
    return selected, modes[selected]


def documents(data: dict) -> tuple[str, ...]:
    return tuple(dict.fromkeys(name for modes in data["profiles"].values()
                               for item in modes.values() for name in item["instructions"]))


def role_files(data: dict) -> set[str]:
    return {PurePosixPath(name).name for modes in data["profiles"].values()
            for item in modes.values() for name in item["roles"]}


def config(root: Path, item: dict) -> dict:
    # The same ordered concatenation can be copied into a native config by hand.
    return tomllib.loads("\n".join(source_text(root, name) for name in item["config"]))


def instructions(root: Path, data: dict, item: dict) -> dict[str, str]:
    result = {}
    begin, end = data["markers"]["begin"], data["markers"]["end"]
    for name, paths in item["instructions"].items():
        parts = [source_text(root, source).strip() for source in paths]
        if any(not part or begin in part or end in part for part in parts):
            raise ValueError("Instruction sources must be nonempty, unmarked fragments")
        result[name] = "\n".join((begin, *parts, end))
    return result
