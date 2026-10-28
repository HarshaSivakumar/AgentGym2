from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PluginBundle:
    agent_name: str
    prompt: str


_PLUGIN_COMPONENTS = {
    "api_design": (
        "API-First-Code-Architect",
        "agents/API-First-Code-Architect.agent.md",
        (
            "skills/contract-first-types/skill.md",
            "skills/validation-schema-designer/skill.md",
            "skills/error-modeler/skill.md",
            "skills/guarded-skeleton-implementations/skill.md",
        ),
    ),
    "api_documentation": (
        "API-Documentation-Generator",
        "agents/API-Documenter.agent.md",
        ("skills/markdown-api-formatter/SKILL.md",),
    ),
}


def load_plugin_bundle(plugin_root: str | Path, mode: str) -> PluginBundle:
    try:
        plugin_folder, agent_file, skill_files = _PLUGIN_COMPONENTS[mode]
    except KeyError as error:
        raise ValueError(f"Unsupported plugin mode: {mode}") from error

    plugin_dir = Path(plugin_root).expanduser().resolve() / plugin_folder
    component_paths = [agent_file, *skill_files]
    contents: list[str] = []
    for relative_path in component_paths:
        path = plugin_dir / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Plugin component not found: {path}")
        contents.append(path.read_text(encoding="utf-8"))

    agent_name = "API-First-Code-Architect" if mode == "api_design" else "API-Documenter"
    return PluginBundle(agent_name=agent_name, prompt="\n\n".join(contents))