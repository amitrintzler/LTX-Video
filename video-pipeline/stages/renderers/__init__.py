"""
stages/renderers/__init__.py — Renderer plugin registry.

Each renderer module must expose:
    render(scene: dict, config: PipelineConfig, out_path: Path) -> Path
"""

# Registry of all known renderer names → module paths.
# Implemented renderers should import cleanly; missing ones raise ModuleNotFoundError.
RENDERERS: dict[str, str] = {
    "manim":          "stages.renderers.manim",
    "motion-canvas":  "stages.renderers.slides",   # slides is the closest text/card renderer
    "d3":             "stages.renderers.d3",
    "html_anim":      "stages.renderers.html_anim",
    "animatediff":    "stages.renderers.animatediff",
    "slides":         "stages.renderers.slides",
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
