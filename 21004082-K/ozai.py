"""
Ozai — Articulated character (simplified, SITTING on throne).

Built from repo primitives (cube / sphere / cylinder OFFs) using a hierarchical
Scenegraph. Ozai is mostly static and stoic — he is positioned on the throne in
the back of the room. Only the head is articulated (used in shot 4 to give a
slight "imperturbable" tilt while speaking).

Hierarchy
---------
    root
    └── ozai_root                  (translate to throne [0, 0.3, -3])
        └── torso                  (translate [0, 0.3, 0] + rotationX -0.1 — sitting)
            ├── torso_visual       (scale [1.0, 1.4, 0.6] cube — robe / torso)
            │   └── torso_mesh
            ├── cuello             (translate [0, 0.7, 0])
            │   └── cuello_visual  (scale [0.3, 0.25, 0.3] cube — neck)
            │       └── cuello_mesh
            │       └── cabeza     (translate [0, 0.25, 0])
            │           └── cabeza_visual  (scale [0.55, 0.75, 0.62] sphere — head)
            │               └── cabeza_mesh
            ├── brazo_der          (translate [0.5, 0.5, 0] + rotationZ for armrest)
            │   └── brazo_der_visual  (scale [0.25, 0.8, 0.25] cube)
            │       └── brazo_der_mesh
            │       └── antebrazo_der (translate [0, -0.8, 0])
            │           └── antebrazo_der_visual  (scale [0.22, 0.75, 0.22] cube)
            │               └── antebrazo_der_mesh
            └── brazo_izq          (translate [-0.5, 0.5, 0] + rotationZ mirrored)
                └── brazo_izq_visual  (scale [0.25, 0.8, 0.25] cube)
                    └── brazo_izq_mesh
                    └── antebrazo_izq (translate [0, -0.8, 0])
                        └── antebrazo_izq_visual  (scale [0.22, 0.75, 0.22] cube)
                            └── antebrazo_izq_mesh

Notes
-----
- The vertex shader declares ``in vec3 color`` but the OFF loader fills the
  buffer with 4-component (RGBA) data. We strip the alpha channel after each
  ``load_and_register_mesh`` (see ``_strip_color_alpha``).
- ``add_object`` builds a transform node + a separate mesh-instance node under
  it.  For the body parts we go with the explicit ``add_transform`` +
  ``add_mesh_instance`` + ``add_edge`` pattern so the visual transform (the
  scale on the part) is a sibling of the joint, which is the only way to have
  a controllable joint with its own mesh attached.
- Compatible with the ``multiple_lights`` shader (Task 4). The pipeline name is
  passed in by the caller so this module does not assume a single pipeline.
"""

import numpy as np

import grafica.transformations as tr
from grafica.scenegraph import Scenegraph


# --------------------------------------------------------------------------- #
# Paleta de la Nación del Fuego
# --------------------------------------------------------------------------- #
# Túnica / torso / brazos → rojo imperial oscuro
ROBE_COLOR = np.array([120, 20, 15, 255], dtype=np.uint8)
# Piel expuesta (cabeza, cuello, manos) → tono cálido
SKIN_COLOR = np.array([220, 180, 140, 255], dtype=np.uint8)

# Posición del trono en la sala (esquina trasera).
THRONE_TRANSLATE = np.array([0.0, 0.3, -3.0], dtype=np.float32)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _strip_color_alpha(graph, mesh_name, force_color):
    """Reescribe el atributo ``color`` a 3 componentes (float32) para
    que coincida con el input ``in vec3 color`` del vertex shader.

    El loader de ``.off`` produce un buffer RGBA uint8 (4 bytes por
    vertice). El buffer GPU para ``vec3 color`` espera 3 floats por
    vertice (12 bytes). Convierte a float32 normalizado [0,1].
    """
    if mesh_name not in graph.meshes:
        return
    children = graph.meshes[mesh_name].get("children", [])
    if not children:
        return
    color_attr = children[0].get("attributes", {}).get("color")
    if color_attr is None or color_attr.size % 4 != 0:
        return
    n_v = color_attr.size // 4
    rgb = np.empty((n_v, 3), dtype=np.float32)
    rgb[:, 0] = force_color[0] / 255.0
    rgb[:, 1] = force_color[1] / 255.0
    rgb[:, 2] = force_color[2] / 255.0
    children[0]["attributes"]["color"] = rgb.flatten()


def _add_limb(graph, pipeline_name, *, parent, joint_name, joint_transform,
              visual_name, visual_scale, mesh_name, mesh_path, color):
    """
    Build a simple limb with the explicit
        parent -> joint -> visual -> mesh
    pattern. ``joint`` carries the articulation transform, ``visual``
    scales the primitive to the part's size, ``mesh`` is the actual draw.
    """
    # 1. Joint transform (parent -> joint)
    graph.add_transform(joint_name, joint_transform)
    graph.add_edge(parent, joint_name)

    # 2. Visual scale (joint -> visual)
    graph.add_transform(visual_name, tr.scale(*visual_scale))
    graph.add_edge(joint_name, visual_name)

    # 3. Mesh instance under visual
    graph.add_mesh_instance(
        mesh_name,
        mesh_path,  # the OFF file name (registered by the caller)
        pipeline_name,
    )
    graph.add_edge(visual_name, mesh_name)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def build_ozai(graph, pipeline_name, parent="root"):
    """
    Attach the Ozai rig to ``graph`` under ``parent``.

    Must be called AFTER:
        * the pipeline is registered (so the mesh instances have a
          valid pipeline to bind to)
        * the OFF meshes (cube, sphere, cylinder) are registered under
          the names ``"cube"``, ``"sphere"`` and ``"cylinder"``
        * the alpha-strip workaround has been applied to those meshes
          (we do that here too — re-strip — to be safe).
    """
    # --- Re-strip the alpha channel on the primitives (idempotent) ---------
    for name in ("cube", "sphere", "cylinder"):
        if name in graph.meshes:
            # We don't know which color the caller wants here; we pick a
            # neutral gray that we will overwrite when we build the parts.
            # The actual colors are forced by re-wrapping the mesh's first
            # child below.
            pass

    # --- Register (or re-use) a private OFF mesh per part ------------------
    # We re-register with a unique name per part so the color buffer is
    # clean (3-component) and the color matches the body part. This is
    # the same approach as the test_shader workaround: load with
    # force_color, then strip the alpha on the resulting buffer.
    graph.load_and_register_mesh(
        "ozai_torso_cube", "assets/cube.off", force_color=ROBE_COLOR
    )
    _strip_color_alpha(graph, "ozai_torso_cube", ROBE_COLOR)

    graph.load_and_register_mesh(
        "ozai_cuello_cube", "assets/cube.off", force_color=SKIN_COLOR
    )
    _strip_color_alpha(graph, "ozai_cuello_cube", SKIN_COLOR)

    graph.load_and_register_mesh(
        "ozai_head_sphere", "assets/sphere.off", force_color=SKIN_COLOR
    )
    _strip_color_alpha(graph, "ozai_head_sphere", SKIN_COLOR)

    graph.load_and_register_mesh(
        "ozai_arm_cube", "assets/cube.off", force_color=ROBE_COLOR
    )
    _strip_color_alpha(graph, "ozai_arm_cube", ROBE_COLOR)

    # --- ozai_root: position on the throne -------------------------------
    graph.add_transform("ozai_root", tr.translate(*THRONE_TRANSLATE))
    graph.add_edge(parent, "ozai_root")

    # --- torso: slightly tilted back (sitting posture) -------------------
    # The translation lifts the torso to the seated height (≈0.3 above the
    # throne base), and rotationX(-0.1) tilts it slightly backward to
    # suggest a slouched, authoritative sitting pose.
    torso_transform = tr.matmul([
        tr.translate(0.0, 0.3, 0.0),
        tr.rotationX(-0.1),
    ])
    graph.add_transform("ozai_torso", torso_transform)
    graph.add_edge("ozai_root", "ozai_torso")

    # --- torso visual (robe cube) ----------------------------------------
    graph.add_transform("ozai_torso_visual", tr.scale(1.0, 1.4, 0.6))
    graph.add_edge("ozai_torso", "ozai_torso_visual")
    graph.add_mesh_instance(
        "ozai_torso_mesh",
        "ozai_torso_cube",
        pipeline_name,
    )
    graph.add_edge("ozai_torso_visual", "ozai_torso_mesh")

    # --- cuello (neck) ---------------------------------------------------
    graph.add_transform("ozai_cuello", tr.translate(0.0, 0.7, 0.0))
    graph.add_edge("ozai_torso", "ozai_cuello")

    graph.add_transform("ozai_cuello_visual", tr.scale(0.3, 0.25, 0.3))
    graph.add_edge("ozai_cuello", "ozai_cuello_visual")
    graph.add_mesh_instance(
        "ozai_cuello_mesh",
        "ozai_cuello_cube",
        pipeline_name,
    )
    graph.add_edge("ozai_cuello_visual", "ozai_cuello_mesh")

    # --- cabeza (head) — this is the joint that moves in shot 4 ----------
    graph.add_transform("ozai_cabeza", tr.translate(0.0, 0.25, 0.0))
    graph.add_edge("ozai_cuello", "ozai_cabeza")

    graph.add_transform("ozai_cabeza_visual", tr.scale(0.55, 0.75, 0.62))
    graph.add_edge("ozai_cabeza", "ozai_cabeza_visual")
    graph.add_mesh_instance(
        "ozai_cabeza_mesh",
        "ozai_head_sphere",
        pipeline_name,
    )
    graph.add_edge("ozai_cabeza_visual", "ozai_cabeza_mesh")

    # --- brazo_der (right arm) -------------------------------------------
    # Translate out to the shoulder, then rotateZ so the arm rests on the
    # throne armrest pointing slightly downward and outward.
    brazo_der_joint = tr.matmul([
        tr.translate(0.5, 0.5, 0.0),
        tr.rotationZ(-0.4),
    ])
    graph.add_transform("ozai_brazo_der", brazo_der_joint)
    graph.add_edge("ozai_torso", "ozai_brazo_der")

    graph.add_transform("ozai_brazo_der_visual", tr.scale(0.25, 0.8, 0.25))
    graph.add_edge("ozai_brazo_der", "ozai_brazo_der_visual")
    graph.add_mesh_instance(
        "ozai_brazo_der_mesh",
        "ozai_arm_cube",
        pipeline_name,
    )
    graph.add_edge("ozai_brazo_der_visual", "ozai_brazo_der_mesh")

    # --- antebrazo_der (right forearm) ----------------------------------
    graph.add_transform(
        "ozai_antebrazo_der",
        tr.translate(0.0, -0.8, 0.0),
    )
    graph.add_edge("ozai_brazo_der", "ozai_antebrazo_der")

    graph.add_transform(
        "ozai_antebrazo_der_visual", tr.scale(0.22, 0.75, 0.22)
    )
    graph.add_edge("ozai_antebrazo_der", "ozai_antebrazo_der_visual")
    graph.add_mesh_instance(
        "ozai_antebrazo_der_mesh",
        "ozai_arm_cube",
        pipeline_name,
    )
    graph.add_edge("ozai_antebrazo_der_visual", "ozai_antebrazo_der_mesh")

    # --- brazo_izq (left arm) — mirrored ---------------------------------
    brazo_izq_joint = tr.matmul([
        tr.translate(-0.5, 0.5, 0.0),
        tr.rotationZ(0.4),
    ])
    graph.add_transform("ozai_brazo_izq", brazo_izq_joint)
    graph.add_edge("ozai_torso", "ozai_brazo_izq")

    graph.add_transform("ozai_brazo_izq_visual", tr.scale(0.25, 0.8, 0.25))
    graph.add_edge("ozai_brazo_izq", "ozai_brazo_izq_visual")
    graph.add_mesh_instance(
        "ozai_brazo_izq_mesh",
        "ozai_arm_cube",
        pipeline_name,
    )
    graph.add_edge("ozai_brazo_izq_visual", "ozai_brazo_izq_mesh")

    # --- antebrazo_izq (left forearm) ------------------------------------
    graph.add_transform(
        "ozai_antebrazo_izq",
        tr.translate(0.0, -0.8, 0.0),
    )
    graph.add_edge("ozai_brazo_izq", "ozai_antebrazo_izq")

    graph.add_transform(
        "ozai_antebrazo_izq_visual", tr.scale(0.22, 0.75, 0.22)
    )
    graph.add_edge("ozai_antebrazo_izq", "ozai_antebrazo_izq_visual")
    graph.add_mesh_instance(
        "ozai_antebrazo_izq_mesh",
        "ozai_arm_cube",
        pipeline_name,
    )
    graph.add_edge("ozai_antebrazo_izq_visual", "ozai_antebrazo_izq_mesh")


def get_ozai_joints():
    """
    Return the list of joint node keys that the rest of the system can
    animate. Ozai is mostly static — only the torso tilt and the head
    are exposed.
    """
    return ["ozai_torso", "ozai_cabeza"]


def apply_ozai_pose(graph, pose_dict):
    """
    Apply a pose to Ozai by overwriting the transform on the listed
    joints. ``pose_dict`` maps joint name -> 4x4 ``np.ndarray`` (or any
    object that ``add_transform`` accepts as a transform).

    Recognized keys
    ---------------
    ``ozai_torso``   : 4x4 transform. Default (slight backward tilt
                       while sitting) is built into the rig; use this
                       key to override (e.g. to lean forward in shot 2).
    ``ozai_cabeza``  : 4x4 transform. Used in shot 4 to give Ozai a
                       slight head movement while speaking — usually
                       a small ``rotationY``/``rotationZ`` composed
                       with the joint's base translation.

    Any joint listed in ``get_ozai_joints()`` that is NOT in
    ``pose_dict`` keeps its current transform.
    """
    for joint_name, new_transform in pose_dict.items():
        if joint_name not in graph.nodes:
            # Caller passed an unknown key — ignore silently. The whole
            # scene shares one graph; we don't want a typo in one pose
            # dict to break unrelated rigs.
            continue
        graph.nodes[joint_name]["transform"] = np.asarray(
            new_transform, dtype=np.float32
        )
    # Recompute global transforms on next render. Scenegraph.render()
    # does this automatically when ``recalculate_transforms`` is True
    # (the default), so we don't need to call it here.
