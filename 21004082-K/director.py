"""
Director — Cinematic timeline coordinator for the Zuko vs. Ozai scene.

This module is the *playback engine* of the 28-second animation. It does not
build the scene; it drives it frame-by-frame by:

  1. Picking the current shot (hard cut) based on absolute time ``t``.
  2. Asking ``camera.get_camera(shot_index, t_local, aspect)`` for the
     view + projection matrices for that shot (camera.py handles smooth
     zoom within shots 1 and 5 via linear interpolation).
  3. Registering the view on the scene graph and setting the projection +
     ``view_position`` global attributes.
  4. Triggering pose updates on the Zuko and Ozai character rigs
     (lazy-imported so the director can be imported even before those
     modules exist).
  5. Synchronising the lighting uniforms (PointLight + 2 SpotLights +
     Material) by writing **directly to the GLSL pipeline**, because
     ``set_global_attributes`` cannot bind struct-array uniforms
     (see ``issues.md``).

Design rules (see also ``learnings.md``):
  - **Hard cuts** between shots. No interpolation between adjacent shots.
  - **No looping**. When ``t >= 28.0`` we freeze on shot 6 with
    ``t_local = 1.0``.
  - Sibling-module imports only (``from camera import ...``). The caller
    is expected to launch the example with the 21004082-K directory on
    ``sys.path`` / as the working directory.

Shot data mirrors the timeline in ``Escena.md`` and the camera list in
``camera.py``. The pose names in ``SHOTS`` are *logical* identifiers
mapped through ``ZUKO_POSES`` / ``OZAI_POSES`` to the joint-dict
format expected by ``zuko.apply_zuko_pose`` / ``ozai.apply_ozai_pose``.
"""

from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# Sibling-module imports (no os.path juggling — see "MUST NOT DO")
# ---------------------------------------------------------------------------
from camera import get_camera, SHOTS as CAMERA_SHOTS
from lighting import (
    POINT_LIGHT_DEFAULTS,
    SPOTLIGHT_LEFT_DEFAULTS,
    SPOTLIGHT_RIGHT_DEFAULTS,
    MATERIAL_DEFAULTS,
    VIEW_POSITION_DEFAULT,
)


# ---------------------------------------------------------------------------
# Lazy character-pose imports
# ---------------------------------------------------------------------------
# zuko.py and ozai.py are separate tasks (7 and 8) and may not exist yet.
# We provide a no-op fallback so the director is importable in isolation.
try:
    from zuko import apply_zuko_pose as _zuko_apply_raw  # type: ignore
except ImportError:
    def _zuko_apply_raw(graph, pose_dict):  # type: ignore
        """Fallback no-op used when ``zuko.py`` is not yet available."""
        return None


try:
    from ozai import apply_ozai_pose as _ozai_apply_raw  # type: ignore
except ImportError:
    def _ozai_apply_raw(graph, pose_dict):  # type: ignore
        """Fallback no-op used when ``ozai.py`` is not yet available."""
        return None


# ===========================================================================
# Director's shot list
# ===========================================================================
# Each shot references a camera index in camera.SHOTS and a *logical* pose
# identifier for Zuko and Ozai. The actual pose transforms live in
# zuko.py / ozai.py; here we only orchestrate.
#
# Pose catalogue (to be implemented in zuko.py / ozai.py):
#   Zuko:
#       - "espalda_espada"        Zuko from behind, sword down (shot 0)
#       - "estatico"              Static, tense face, no movement (shot 1)
#       - "apunta_espada"         Sword raised, pointing at "camera" (shot 2)
#       - "fuera_cuadro"          Off-screen (shot 3 is on Ozai, Zuko idle)
#       - "perfil_rabia"          Left profile + contained rage (shot 4)
#       - "desenvaina_segunda"    Pass sword to left hand, draw second
#                                 sword, combat stance (shot 5)
#       - "determinacion"         Head + shoulders gesturing, conviction
#                                 (shot 6)
#   Ozai:
#       - "sentado"               Default seated pose on the throne
#       - "sentado_cabeza"        Seated with subtle head movement (shot 4)
# ---------------------------------------------------------------------------

SHOTS = [
    # Shot 0 — 0-1s    Plano general (sobre el hombro de Zuko)
    {
        "start": 0.0,
        "end": 1.0,
        "camera_index": 0,
        "zuko_pose": "espalda_espada",
        "ozai_pose": "sentado",
    },
    # Shot 1 — 1-7s    Zoom in lento (plano medio → primer plano)
    {
        "start": 1.0,
        "end": 7.0,
        "camera_index": 1,
        "zuko_pose": "estatico",
        "ozai_pose": "sentado",
    },
    # Shot 2 — 7-11s   Plano medio (Zuko apunta la espada a la cámara)
    {
        "start": 7.0,
        "end": 11.0,
        "camera_index": 2,
        "zuko_pose": "apunta_espada",
        "ozai_pose": "sentado",
    },
    # Shot 3 — 11-16s  Primer plano de Ozai (Zuko fuera de cuadro)
    {
        "start": 11.0,
        "end": 16.0,
        "camera_index": 3,
        "zuko_pose": "fuera_cuadro",
        "ozai_pose": "sentado",
    },
    # Shot 4 — 16-20s  Perfil y contraplano (Zuko rabioso, Ozai mueve cabeza)
    {
        "start": 16.0,
        "end": 20.0,
        "camera_index": 4,
        "zuko_pose": "perfil_rabia",
        "ozai_pose": "sentado_cabeza",
    },
    # Shot 5 — 20-25s  Zoom out leve — Zuko desenvaina segunda espada
    {
        "start": 20.0,
        "end": 25.0,
        "camera_index": 5,
        "zuko_pose": "desenvaina_segunda",
        "ozai_pose": "sentado",
    },
    # Shot 6 — 25-28s  Contrapicado — Zuko habla con determinación
    {
        "start": 25.0,
        "end": 28.0,
        "camera_index": 6,
        "zuko_pose": "determinacion",
        "ozai_pose": "sentado",
    },
]


# Total runtime — kept as a module constant so callers don't have to dig
# through the SHOTS list.
TOTAL_DURATION = SHOTS[-1]["end"]


# ===========================================================================
# Pose registry (logical name -> joint-dict)
# ===========================================================================
# ``zuko.apply_zuko_pose`` / ``ozai.apply_ozai_pose`` accept a
# ``{joint_name: 4x4 transform}`` dict. We expose a *name*-based API on
# top of that for the timeline: a pose name in SHOTS is looked up here
# to get the actual joint dict to pass through.
#
# The transforms are simple joint rotations / mirrors. The exact values
# are intentionally conservative — they only need to *visually convey*
# the pose; the dramatic effect comes from the camera cuts.

# Lazy import of tr only where needed (avoids an import-time cost).
def _tr():
    import grafica.transformations as tr  # local import to keep top cheap
    return tr


# ---------------------------------------------------------------------------
# Zuko poses
# ---------------------------------------------------------------------------
# Zuko's joint list (from zuko.get_zuko_joints):
#   torso, cabeza, brazo_der, antebrazo_der, mano_der,
#   brazo_izq, antebrazo_izq, mano_izq,
#   muslo_der, pantorrilla_der, muslo_izq, pantorrilla_izq
#
# The rest pose has the right arm relaxed at the side with a sword
# pointing down (the canonical "from-behind" pose used in shot 0).
# Most shots only override a few joints; an empty dict means "rest pose".
ZUKO_POSES: dict = {
    # Shot 0: Zuko de espaldas, espada hacia abajo. Rest pose.
    "espalda_espada": {},

    # Shot 1: estático, ceño fruncido — slight turn toward camera.
    "estatico": {
        "cabeza": _tr().rotationY(0.15),
    },

    # Shot 2: apunta con la espada a la cámara (right arm extended).
    "apunta_espada": {
        "brazo_der": _tr().rotationX(-np.pi / 2),     # raise arm forward
        "antebrazo_der": _tr().rotationX(-0.2),        # straighten
    },

    # Shot 3: Zuko no aparece — la cámara está sobre Ozai. Rest pose
    # (the camera doesn't see him, but the rig is still being driven —
    # keeps the joints consistent for the next shot).
    "fuera_cuadro": {},

    # Shot 4: perfil de rabia contenida.
    "perfil_rabia": {
        "cabeza": _tr().rotationY(-0.3),     # look to the side
        "torso": _tr().rotationY(-0.1),
    },

    # Shot 5: pasa la espada a la mano izquierda, desenvaina la
    # segunda, postura de combate.
    "desenvaina_segunda": {
        "brazo_der": _tr().rotationX(-np.pi / 2.5),     # raised, sword out
        "antebrazo_der": _tr().rotationX(-0.4),
        "brazo_izq": _tr().rotationX(-np.pi / 3),       # left arm forward
        "antebrazo_izq": _tr().rotationX(-0.3),
        "muslo_der": _tr().rotationX(0.15),             # combat stance
        "muslo_izq": _tr().rotationX(-0.15),
        "pantorrilla_der": _tr().rotationX(-0.2),
        "pantorrilla_izq": _tr().rotationX(0.2),
    },

    # Shot 6: determinación — gesticula con cabeza y hombros.
    "determinacion": {
        "cabeza": _tr().rotationX(-0.15),     # chin up
        "torso": _tr().rotationX(-0.05),      # slight lean back
    },
}


# ---------------------------------------------------------------------------
# Ozai poses
# ---------------------------------------------------------------------------
# Ozai's joint list (from ozai.get_ozai_joints):
#   ozai_torso, ozai_cabeza
#
# Ozai is mostly static — only the torso and head move.
OZAI_POSES: dict = {
    # Default seated pose: no overrides (rest pose is already seated).
    "sentado": {},

    # Shot 4: ligero movimiento de cabeza mientras habla.
    "sentado_cabeza": {
        "ozai_cabeza": _tr().rotationY(0.08),
    },
}


# ===========================================================================
# Shot selection
# ===========================================================================

def get_current_shot(t: float):
    """
    Return the active shot and the local time within it.

    Parameters
    ----------
    t : float
        Absolute time in seconds. Values outside ``[0, 28]`` are *clamped*
        (we don't loop — we freeze on the last/first shot).

    Returns
    -------
    shot : dict
        The shot definition (see ``SHOTS``).
    t_local : float
        Normalised time within the shot, ``(t - start) / (end - start)``,
        clamped to ``[0, 1]``.

    Notes
    -----
    * When ``t < 0`` we return the first shot with ``t_local = 0``.
    * When ``t >= 28.0`` we return the last shot with ``t_local = 1``.
    * Boundaries are inclusive at the start: a shot's ``start`` belongs
      to that shot. We do not interpolate across the boundary — it is a
      *hard cut* (the camera changes instantly).
    """
    if t < 0.0:
        return SHOTS[0], 0.0
    if t >= TOTAL_DURATION:
        return SHOTS[-1], 1.0

    for shot in SHOTS:
        start, end = shot["start"], shot["end"]
        if start <= t < end:
            t_local = (t - start) / (end - start)
            # Defensive clamp — should already be in [0, 1) but guards
            # against floating point wobble at shot boundaries.
            t_local = max(0.0, min(1.0, t_local))
            return shot, t_local

    # Unreachable: the TOTAL_DURATION check above covers the upper end.
    return SHOTS[-1], 1.0


# ===========================================================================
# Helpers
# ===========================================================================

def _eye_from_view(view: np.ndarray) -> np.ndarray:
    """
    Recover the camera world-space position from a 4x4 view matrix.

    The view matrix is the inverse of the camera's local-to-world
    transform. For a lookAt-style view matrix the upper-left 3x3 is a
    rotation, so::

        eye = - R^T @ t
            = -view[:3, :3].T @ view[:3, 3]

    Used to feed the ``view_position`` uniform in the fragment shader
    (needed for specular computation).
    """
    return -view[:3, :3].T @ view[:3, 3]


def _resolve_pose(name: str, registry: dict, rig_label: str) -> dict:
    """
    Look up a logical pose name in a registry, returning an empty dict
    if it isn't found. We never crash the timeline for an unknown
    pose — we just log and let the rig keep its rest pose.
    """
    pose = registry.get(name)
    if pose is None:
        print(f"[WARN] {rig_label} pose '{name}' no está definida; usando rest pose")
        return {}
    return pose


# ===========================================================================
# Per-frame scene update
# ===========================================================================

def update_scene(graph, t: float, width: int, height: int) -> None:
    """
    Drive the camera, view_position, and character poses for time ``t``.

    Parameters
    ----------
    graph : Scenegraph
        The shared scene graph. Expected to already have:
        * the ``lit`` pipeline registered (so the lighting bindings
          resolve), and
        * the Zuko / Ozai rigs attached (the ``apply_*_pose`` fallbacks
          are no-ops if the rig isn't there, which keeps the director
          importable in isolation).
    t : float
        Absolute time in seconds. ``update_scene`` clamps it via
        ``get_current_shot``.
    width, height : int
        Window dimensions used to compute the projection aspect ratio.

    Side effects
    ------------
    1. Resolves the current shot and the camera's view + projection
       matrices.
    2. Registers the view (becomes ``graph.current_view``).
    3. Writes the projection and ``view_position`` global attributes.
    4. Recomputes the global transforms on the graph.
    5. Triggers Zuko and Ozai pose updates.
    """
    shot, t_local = get_current_shot(t)

    aspect = float(width) / float(height) if height else 1.0
    view, projection = get_camera(shot["camera_index"], t_local, aspect)

    # 2. Register the view (becomes current by default — see scenegraph.py).
    graph.register_view_transform(view)

    # 3. Projection + camera position. ``view_position`` must follow the
    #    camera (so specular reflects correctly); we recover it from the
    #    view matrix.
    eye = _eye_from_view(view)
    graph.set_global_attributes(
        projection=projection,
        view_position=eye.astype(np.float32),
    )

    # 4. Recompute world-space transforms so the next render reflects the
    #    new view/pose. (``render()`` also does this lazily, but we call
    #    it explicitly so a pose change is observable even if the
    #    consumer reads ``graph.global_transforms`` between updates.)
    graph.calculate_global_transforms()

    # 5. Apply character poses. The rig's ``apply_*_pose`` expects a
    #    joint-dict, so we resolve the logical name to that dict first.
    zuko_pose_dict = _resolve_pose(shot["zuko_pose"], ZUKO_POSES, "Zuko")
    ozai_pose_dict = _resolve_pose(shot["ozai_pose"], OZAI_POSES, "Ozai")
    _zuko_apply_raw(graph, zuko_pose_dict)
    _ozai_apply_raw(graph, ozai_pose_dict)


# ===========================================================================
# Per-frame lighting update
# ===========================================================================

def _set_point_light(pipeline, prefix: str, light: dict) -> None:
    """Upload a PointLight's fields to the GLSL struct-array slot."""
    import pyglet.graphics.shader
    try:
        pipeline[f"{prefix}.position"] = light["position"]
        pipeline[f"{prefix}.constant"] = light["constant"]
        pipeline[f"{prefix}.linear"] = light["linear"]
        pipeline[f"{prefix}.quadratic"] = light["quadratic"]
        pipeline[f"{prefix}.ambient"] = light["ambient"]
        pipeline[f"{prefix}.diffuse"] = light["diffuse"]
        pipeline[f"{prefix}.specular"] = light["specular"]
    except pyglet.graphics.shader.ShaderException as e:
        print(f"[WARN] No se pudo subir PointLight {prefix}: {e}")


def _set_spot_light(pipeline, prefix: str, light: dict) -> None:
    """Upload a SpotLight's fields to the GLSL struct-array slot."""
    import pyglet.graphics.shader
    try:
        pipeline[f"{prefix}.position"] = light["position"]
        pipeline[f"{prefix}.direction"] = light["direction"]
        pipeline[f"{prefix}.cutOff"] = light["cutOff"]
        pipeline[f"{prefix}.outerCutOff"] = light["outerCutOff"]
        pipeline[f"{prefix}.constant"] = light["constant"]
        pipeline[f"{prefix}.linear"] = light["linear"]
        pipeline[f"{prefix}.quadratic"] = light["quadratic"]
        pipeline[f"{prefix}.ambient"] = light["ambient"]
        pipeline[f"{prefix}.diffuse"] = light["diffuse"]
        pipeline[f"{prefix}.specular"] = light["specular"]
    except pyglet.graphics.shader.ShaderException as e:
        print(f"[WARN] No se pudo subir SpotLight {prefix}: {e}")


def _set_material(pipeline, material: dict) -> None:
    """Upload the Material struct fields to the GLSL shader."""
    import pyglet.graphics.shader
    try:
        pipeline["material.ambient"] = material["ambient"]
        pipeline["material.diffuse"] = material["diffuse"]
        pipeline["material.specular"] = material["specular"]
        pipeline["material.shininess"] = material["shininess"]
    except pyglet.graphics.shader.ShaderException as e:
        print(f"[WARN] No se pudo subir Material: {e}")


# Pipeline name used by the scene. Kept as a module constant so the
# caller can override it before invoking ``update_lighting_pipeline``
# (or — more simply — pass the pipeline name explicitly).
DEFAULT_PIPELINE_NAME = "lit"


def update_lighting_pipeline(
    graph,
    t: float,
    pipeline_name: str = DEFAULT_PIPELINE_NAME,
) -> None:
    """
    Push lighting uniforms directly to the GPU pipeline.

    The point/spot/material structs are bound one field at a time
    because ``set_global_attributes`` silently swallows ShaderException
    for struct-array uniforms (see ``issues.md``). The signature takes
    ``t`` (in seconds) so the API mirrors ``update_scene`` and to leave
    room for time-driven lighting (e.g. flicker) in a future iteration;
    for now the lighting state is constant across the whole 28 s.

    Parameters
    ----------
    graph : Scenegraph
        The scene graph (must contain a pipeline registered as
        ``pipeline_name``).
    t : float
        Absolute time in seconds (currently unused — kept for API
        symmetry with ``update_scene``).
    pipeline_name : str, optional
        Name of the registered pipeline to bind. Defaults to ``"lit"``.
    """
    pipeline = graph.pipelines.get(pipeline_name)
    if pipeline is None:
        # The pipeline isn't ready yet (e.g. the example hasn't finished
        # setup). Skip silently — the next frame will retry.
        return

    _set_point_light(pipeline, "pointLights[0]", POINT_LIGHT_DEFAULTS)
    _set_spot_light(pipeline, "spotLights[0]", SPOTLIGHT_LEFT_DEFAULTS)
    _set_spot_light(pipeline, "spotLights[1]", SPOTLIGHT_RIGHT_DEFAULTS)
    _set_material(pipeline, MATERIAL_DEFAULTS)


# ===========================================================================
# Smoke test
# ===========================================================================
# A minimal self-check that doesn't require pyglet / OpenGL. It exercises
# the deterministic logic: shot selection, t_local clamping, and the
# camera-position-from-view recovery. Useful to run after editing this
# file::
#
#     uv run python 21004082-K/director.py
#
if __name__ == "__main__":
    print(f"SHOTS: {len(SHOTS)}  TOTAL_DURATION: {TOTAL_DURATION:.1f}s")

    # --- Boundary checks ---------------------------------------------------
    cases = [
        (-0.5, 0, 0.0),    # before start  → first shot
        (0.0, 0, 0.0),     # exact start of shot 0
        (0.5, 0, 0.5),     # mid shot 0
        (1.0, 1, 0.0),     # exact start of shot 1
        (4.0, 1, 0.5),     # mid shot 1
        (7.0, 2, 0.0),     # exact start of shot 2
        (28.0, 6, 1.0),    # exact end → last shot, frozen
        (999.0, 6, 1.0),   # way past end → last shot, frozen
    ]
    print("\n[get_current_shot]")
    for t, expected_idx, _ in cases:
        shot, t_local = get_current_shot(t)
        idx = SHOTS.index(shot)
        ok = "OK" if idx == expected_idx else "FAIL"
        print(f"  t={t:>6.2f}  -> shot={idx} t_local={t_local:.3f}  [{ok}]")

    # --- Eye-from-view recovery -------------------------------------------
    print("\n[_eye_from_view]")
    import grafica.transformations as tr
    for eye_in in (
        np.array([1.0, 2.0, 3.0], dtype=np.float32),
        np.array([-1.5, 1.5, 3.5], dtype=np.float32),
        np.array([0.0, 0.3, 2.0], dtype=np.float32),
    ):
        view = tr.lookAt(eye_in, np.array([0.0, 0.0, 0.0], dtype=np.float32),
                         np.array([0.0, 1.0, 0.0], dtype=np.float32))
        eye_out = _eye_from_view(view)
        err = float(np.linalg.norm(eye_out - eye_in))
        print(f"  eye_in={eye_in}  eye_out={eye_out}  err={err:.2e}")

    # --- Shot coverage -----------------------------------------------------
    print("\n[shot coverage]")
    expected_cameras = [0, 1, 2, 3, 4, 5, 6]
    expected_zuko = ["espalda_espada", "estatico", "apunta_espada",
                     "fuera_cuadro", "perfil_rabia", "desenvaina_segunda",
                     "determinacion"]
    expected_ozai = ["sentado", "sentado", "sentado", "sentado",
                     "sentado_cabeza", "sentado", "sentado"]
    for i, shot in enumerate(SHOTS):
        cam_ok = shot["camera_index"] == expected_cameras[i]
        zuko_ok = shot["zuko_pose"] == expected_zuko[i]
        ozai_ok = shot["ozai_pose"] == expected_ozai[i]
        ok = "OK" if (cam_ok and zuko_ok and ozai_ok) else "FAIL"
        print(f"  shot {i}: cam={shot['camera_index']}  "
              f"zuko={shot['zuko_pose']}  ozai={shot['ozai_pose']}  [{ok}]")

    # --- Pose registry coverage --------------------------------------------
    print("\n[pose registry]")
    for name in expected_zuko:
        present = name in ZUKO_POSES
        print(f"  ZUKO_POSES['{name}']: {'present' if present else 'MISSING'}")
    for name in set(expected_ozai):
        present = name in OZAI_POSES
        print(f"  OZAI_POSES['{name}']: {'present' if present else 'MISSING'}")

    print("\nDone.")
