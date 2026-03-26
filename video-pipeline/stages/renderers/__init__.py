"""
stages/renderers/__init__.py — Renderer plugin registry.

Each renderer module must expose:
    render(scene: dict, config: PipelineConfig, out_path: Path) -> Path
"""

# Registry of all known renderer names → module paths.
# Modules for Sub-projects 2 and 3 will raise ModuleNotFoundError until implemented.
RENDERERS: dict[str, str] = {
    "manim":        "stages.renderers.manim",
    "html_anim":    "stages.renderers.html_anim",
    "animatediff":  "stages.renderers.animatediff",
    "slides":       "stages.renderers.slides",
}


def get_renderer(name: str):
    """Return the renderer module for the given name.

    Raises ValueError for unknown renderers.
    Raises ModuleNotFoundError if the renderer module is not yet implemented.
    """
    import importlib
    if name not in RENDERERS:
        raise ValueError(
            f"Unknown renderer: '{name}'. Valid renderers: {sorted(RENDERERS)}"
        )
    return importlib.import_module(RENDERERS[name])
