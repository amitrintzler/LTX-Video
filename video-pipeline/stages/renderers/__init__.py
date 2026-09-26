"""
stages/renderers/__init__.py — Renderer plugin registry.

Each renderer module must expose:
    render(scene: dict, config: PipelineConfig, out_path: Path) -> Path
"""

# Registry of all known renderer names → module paths.
# Implemented renderers should import cleanly; missing ones raise ModuleNotFoundError.
RENDERERS: dict[str, str] = {
    "manim":          "stages.renderers.manim",
    # No Motion Canvas renderer exists. This alias only keeps older scripts
    # loadable; it renders completely static frames, so nothing should choose
    # it for new work - script.py offers "slides" instead, which says so.
    "motion-canvas":  "stages.renderers.slides",
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
