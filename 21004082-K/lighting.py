"""
Lighting configuration module for the multiple_lights shader.

Configures 1 PointLight (overhead ambient) + 2 SpotLights (torch left/right)
with warm Fire Nation orange/red tones.

Flat array layouts (for set_global_attributes / pipeline uniform binding):
  PointLight (15 floats): [pos.xyz, constant, linear, quadratic, ambient.rgb, diffuse.rgb, specular.rgb]
  SpotLight  (20 floats): [pos.xyz, dir.xyz, cutOff, outerCutOff, constant, linear, quadratic, ambient.rgb, diffuse.rgb, specular.rgb]

NOTE: The shader uses struct array uniforms like ``pointLights[0]``, ``spotLights[0]``,
``material.ambient``, etc., but ``set_global_attributes()`` keyword argument names cannot contain
brackets or dots. The underscore-based names (e.g. ``pointLights_0``, ``material_ambient``)
are only global_attributes dict keys --- they will NOT match the actual GLSL uniform names.
If setting via ``set_global_attributes`` raises a ShaderException (silently caught), the
workaround is to bind uniforms directly in the update loop:

    pipeline = graph.pipelines["my_pipeline"]
    pipeline["pointLights[0].position"] = POINT_LIGHT_DEFAULTS["position"].reshape(3, 1, order="F")
    pipeline["pointLights[0].constant"] = POINT_LIGHT_DEFAULTS["constant"]
    ...
"""

import numpy as np


# =============================================================================
# Default camera position
# =============================================================================

VIEW_POSITION_DEFAULT = np.array([0.0, 2.0, 4.0], dtype=np.float32)

# =============================================================================
# PointLight — overhead warm fill light  (15 floats)
# =============================================================================

POINT_LIGHT_DEFAULTS = {
    "position": np.array([0.0, 4.0, 0.0], dtype=np.float32),
    "constant": np.float32(1.0),
    "linear": np.float32(0.09),
    "quadratic": np.float32(0.032),
    # Fire Nation warm tones: R > G >> B
    "ambient": np.array([0.15, 0.08, 0.03], dtype=np.float32),
    "diffuse": np.array([0.80, 0.40, 0.15], dtype=np.float32),
    "specular": np.array([0.50, 0.25, 0.10], dtype=np.float32),
}

# =============================================================================
# SpotLight helpers
# =============================================================================


def _normalize(v):
    """Return normalized copy of *v* as float32."""
    v = np.asarray(v, dtype=np.float32)
    return v / np.linalg.norm(v)


_CENTER = np.array([0.0, 0.0, 0.0], dtype=np.float32)

# =============================================================================
# SpotLight — left torch  (20 floats)
# =============================================================================

SPOTLIGHT_LEFT_DEFAULTS = {
    "position": np.array([-2.0, 2.0, -1.0], dtype=np.float32),
    # direction toward center of scene
    "direction": _normalize(_CENTER - np.array([-2.0, 2.0, -1.0])),
    "cutOff": np.float32(np.cos(np.radians(15.0))),
    "outerCutOff": np.float32(np.cos(np.radians(25.0))),
    "constant": np.float32(1.0),
    "linear": np.float32(0.09),
    "quadratic": np.float32(0.032),
    "ambient": np.array([0.15, 0.08, 0.03], dtype=np.float32),
    "diffuse": np.array([0.80, 0.40, 0.15], dtype=np.float32),
    "specular": np.array([0.50, 0.25, 0.10], dtype=np.float32),
}

# =============================================================================
# SpotLight — right torch  (20 floats)
# =============================================================================

SPOTLIGHT_RIGHT_DEFAULTS = {
    "position": np.array([2.0, 2.0, -1.0], dtype=np.float32),
    # direction toward center of scene
    "direction": _normalize(_CENTER - np.array([2.0, 2.0, -1.0])),
    "cutOff": np.float32(np.cos(np.radians(15.0))),
    "outerCutOff": np.float32(np.cos(np.radians(25.0))),
    "constant": np.float32(1.0),
    "linear": np.float32(0.09),
    "quadratic": np.float32(0.032),
    "ambient": np.array([0.15, 0.08, 0.03], dtype=np.float32),
    "diffuse": np.array([0.80, 0.40, 0.15], dtype=np.float32),
    "specular": np.array([0.50, 0.25, 0.10], dtype=np.float32),
}

# =============================================================================
# Material defaults — warm metallic
# =============================================================================

MATERIAL_DEFAULTS = {
    "ambient": np.array([0.20, 0.10, 0.05], dtype=np.float32),
    "diffuse": np.array([0.80, 0.40, 0.20], dtype=np.float32),
    "specular": np.array([0.60, 0.30, 0.10], dtype=np.float32),
    "shininess": np.float32(32.0),
}

# =============================================================================
# Array builders
# =============================================================================


def build_point_light_array(light_dict):
    """
    Build a flat float32 array from a PointLight parameter dict.

    Layout (15 floats)::

        [position.xyz, constant, linear, quadratic,
         ambient.rgb,  diffuse.rgb, specular.rgb]

    Matches the GLSL struct in ``fragment_program.glsl``.
    """
    return np.array(
        [
            *light_dict["position"],       # 3
            light_dict["constant"],         # 1
            light_dict["linear"],          # 1
            light_dict["quadratic"],       # 1
            *light_dict["ambient"],         # 3
            *light_dict["diffuse"],         # 3
            *light_dict["specular"],        # 3
        ],
        dtype=np.float32,
    )  # total = 15


def build_spot_light_array(light_dict):
    """
    Build a flat float32 array from a SpotLight parameter dict.

    Layout (20 floats)::

        [position.xyz, direction.xyz, cutOff, outerCutOff,
         constant, linear, quadratic,
         ambient.rgb, diffuse.rgb, specular.rgb]

    Matches the GLSL struct in ``fragment_program.glsl``.

    Note on size
    ------------
    The struct has 20 scalar fields (3+3+1+1+1+1+1+3+3+3 = 20).
    If the OpenGL driver expects a padded layout (e.g. 26 floats due to std140
    alignment), pad to 26 with ``np.pad(..., (0, 6), constant_values=0)``
    before passing to ``pipeline["spotLights[0]"]``.
    """
    return np.array(
        [
            *light_dict["position"],        # 3
            *light_dict["direction"],       # 3
            light_dict["cutOff"],           # 1
            light_dict["outerCutOff"],      # 1
            light_dict["constant"],         # 1
            light_dict["linear"],           # 1
            light_dict["quadratic"],        # 1
            *light_dict["ambient"],          # 3
            *light_dict["diffuse"],          # 3
            *light_dict["specular"],         # 3
        ],
        dtype=np.float32,
    )  # total = 20


# =============================================================================
# Scene graph setup
# =============================================================================


def setup_lighting(
    graph,
    view_position=None,
    point_light=None,
    spot_left=None,
    spot_right=None,
    material=None,
):
    """
    Set lighting **data** on a Scenegraph via ``set_global_attributes``.

    Because the shader uses struct-array uniforms (e.g. ``pointLights[0]``,
    ``material.ambient``) and Python keyword arguments cannot contain ``[`` / ``.``,
    the keys stored in ``global_attributes`` use underscores as a proxy
    (``pointLights_0``, ``material_ambient``, …).

    These keys will **not** match the actual GLSL uniform names, so
    ``pipeline[attr]`` will raise a silently caught ``ShaderException``.
    **The real uniform binding must happen in your update loop**, for example::

        pl = POINT_LIGHT_DEFAULTS
        pipeline = graph.pipelines["my_pipeline"]
        pipeline["pointLights[0].position"] = pl["position"].reshape(3, 1, order="F")
        pipeline["pointLights[0].constant"] = pl["constant"]
        ...

    Parameters
    ----------
    graph : Scenegraph
        The scene graph to configure.
    view_position : np.ndarray | None
        Camera position (3 floats).  Defaults to ``VIEW_POSITION_DEFAULT``.
    point_light : dict | None
        PointLight parameters.       Defaults to ``POINT_LIGHT_DEFAULTS``.
    spot_left : dict | None
        Left-spotlight parameters.    Defaults to ``SPOTLIGHT_LEFT_DEFAULTS``.
    spot_right : dict | None
        Right-spotlight parameters.   Defaults to ``SPOTLIGHT_RIGHT_DEFAULTS``.
    material : dict | None
        Material parameters (keys ``ambient``, ``diffuse``, ``specular``,
        ``shininess``).  Defaults to ``MATERIAL_DEFAULTS``.
    """
    if view_position is None:
        view_position = VIEW_POSITION_DEFAULT
    if point_light is None:
        point_light = POINT_LIGHT_DEFAULTS
    if spot_left is None:
        spot_left = SPOTLIGHT_LEFT_DEFAULTS
    if spot_right is None:
        spot_right = SPOTLIGHT_RIGHT_DEFAULTS
    if material is None:
        material = MATERIAL_DEFAULTS

    graph.set_global_attributes(
        view_position=view_position.astype(np.float32),
        pointLights_0=build_point_light_array(point_light),
        spotLights_0=build_spot_light_array(spot_left),
        spotLights_1=build_spot_light_array(spot_right),
        material_ambient=material["ambient"].astype(np.float32),
        material_diffuse=material["diffuse"].astype(np.float32),
        material_specular=material["specular"].astype(np.float32),
        material_shininess=np.float32(material["shininess"]),
    )
