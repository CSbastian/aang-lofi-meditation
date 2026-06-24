"""
Zuko - Articulated character (standing, dual-wielding broadswords).

Built from repo primitives (``assets/cube.off``, ``assets/sphere.off``,
``assets/cylinder.off``) using a hierarchical ``Scenegraph``. Follows the
Programa.md articulation pattern exactly: a parent ``torso`` joint with
``torso -> {cuello, brazos, piernas}`` sub-trees, each part having its own
``joint -> visual -> mesh`` chain.

Hierarchy
---------
    root
    +-- zuko_root                        (translate [0, 0, 2] - foreground)
        +-- torso                        (identity)
            +-- torso_visual             (scale cube [0.8, 1.2, 0.5])
            |   +-- torso_mesh
            +-- cuello                   (translate [0, 0.6, 0])
            |   +-- cuello_visual        (scale [0.25, 0.2, 0.25])
            |       +-- cuello_mesh
            +-- cabeza                   (translate [0, 0.9, 0])
            |   +-- cabeza_visual        (scale sphere [0.45, 0.62, 0.52])
            |       +-- cabeza_mesh
            +-- brazo_der                (translate [0.4, 0.55, 0], rotZ +pi/2)
            |   +-- brazo_der_visual     (scale [0.2, 0.7, 0.2])
            |       +-- brazo_der_mesh
            |   +-- antebrazo_der        (translate [0, -0.7, 0])
            |       +-- antebrazo_der_visual (scale [0.18, 0.7, 0.18])
            |       |   +-- antebrazo_der_mesh
            |       +-- mano_der         (translate [0, -0.7, 0])
            |           +-- mano_der_visual (scale [0.2, 0.15, 0.2])
            |           |   +-- mano_der_mesh
            |           +-- espada_der    (translate [0, -0.3, 0.15])
            |               +-- espada_der_visual (scale [0.05, 0.05, 1.2])
            |                   +-- espada_der_mesh
            +-- brazo_izq                (mirrored)
            |   +-- brazo_izq_visual
            |   +-- antebrazo_izq
            |   +-- mano_izq
            |       +-- espada_izq
            +-- muslo_der                (translate [0.2, -0.6, 0])
            |   +-- muslo_der_visual     (scale [0.25, 0.85, 0.25])
            |   +-- pantorrilla_der      (translate [0, -0.85, 0])
            |       +-- pantorrilla_der_visual (scale [0.2, 0.8, 0.2])
            |       +-- pie_der          (translate [0, -0.8, 0.15])
            |           +-- pie_der_visual (scale [0.3, 0.25, 0.6])
            +-- muslo_izq                (mirrored)

Notes
-----
- The vertex shader declares ``in vec3 color`` but the OFF loader fills the
  buffer with 4-component (RGBA) data. We strip the alpha channel after each
  ``load_and_register_mesh`` (see ``_strip_color_alpha``), mirroring the
  workaround in ``test_shader.py`` lines 162-172.
- Each body part registers its own OFF mesh (e.g. ``zuko_torso_cube``) so
  the color buffer is unique to that part - the shader's per-vertex color
  is effectively a static material at the moment.
- Compatible with the ``multiple_lights`` shader (Task 4). The pipeline name
  is passed in by the caller so this module does not assume a single
  pipeline.
- Zuko faces +Z (away from the camera, toward the throne / Ozai) by default.
"""

import numpy as np

import grafica.transformations as tr
from grafica.scenegraph import Scenegraph


# --------------------------------------------------------------------------- #
# Paleta de la Nacion del Fuego (RGBA, uint8)
# --------------------------------------------------------------------------- #
# Uniforme principal: torso, biceps, muslos -> rojo oscuro imperial.
FIRE_RED = np.array([180, 30, 30, 255], dtype=np.uint8)
# Piel expuesta: cara, cuello, antebrazos, manos.
SKIN = np.array([230, 190, 150, 255], dtype=np.uint8)
# Pantalones: rojo mas oscuro que el torso.
PANTS = np.array([100, 20, 20, 255], dtype=np.uint8)
# Botas / pies: gris oscuro.
BOOTS = np.array([50, 50, 50, 255], dtype=np.uint8)
# Espadas: acero / plata.
STEEL = np.array([180, 180, 180, 255], dtype=np.uint8)

# Zuko se para en primer plano, al fondo de la sala (frente al trono).
# z=+2 lo deja entre la camara y el trono en z=-3.
ZUKO_TRANSLATE = np.array([0.0, 0.0, 2.0], dtype=np.float32)


# --------------------------------------------------------------------------- #
# Almacenamiento de las transformaciones base (T-pose / pose neutra) de cada
# articulacion. Se rellena en ``build_zuko`` y se consume en
# ``apply_zuko_pose`` para que cada llamada componga
# ``original @ pose_rotation`` en lugar de sobrescribir directamente. Esto
# permite que el caller pase poses parciales: las articulaciones que no
# aparecen en ``pose_dict`` vuelven a la pose neutra al componer con
# ``tr.identity()``.
#
# Se indexa por ``id(graph)`` para que dos rigs distintos (o dos grafos en
# la misma sesion) no compartan la cache de originales por accidente.
# --------------------------------------------------------------------------- #
_ZUKO_ORIGINAL_TRANSFORMS: dict = {}


def _record_originals(graph: Scenegraph) -> None:
    """
    Snapshot every joint's rest-pose transform into the module-level
    cache ``_ZUKO_ORIGINAL_TRANSFORMS[id(graph)]``. Called once at the
    end of ``build_zuko`` so ``apply_zuko_pose`` can compose
    ``original @ pose_dict.get(joint, tr.identity())`` and a partial
    pose dict leaves the un-mentioned joints at the rest pose.
    """
    cache: dict = {}
    for joint in get_zuko_joints():
        if joint in graph.nodes:
            cache[joint] = np.array(
                graph.nodes[joint]["transform"], dtype=np.float32, copy=True
            )
    _ZUKO_ORIGINAL_TRANSFORMS[id(graph)] = cache


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _strip_color_alpha(graph, mesh_name, force_color):
    """
    After ``load_and_register_mesh(..., force_color=...)`` the registered
    ``children[0]['attributes']['color']`` is a 4-component buffer
    (RGBA, ``c4B``), but our vertex shader declares ``in vec3 color``.
    We rewrite that buffer to a flat 3-component (RGB) array with the
    requested color so the GPU upload size matches the shader input.

    Mirrors the workaround in ``test_shader.py`` lines 162-172 and
    ``environment.py`` (Task 2).
    """
    if mesh_name not in graph.meshes:
        return
    children = graph.meshes[mesh_name].get("children", [])
    if not children:
        return
    color_attr = children[0].get("attributes", {}).get("color")
    if color_attr is None:
        return
    # 4-component RGBA buffer: size is a multiple of 4.
    if color_attr.size % 4 != 0:
        return
    n_v = color_attr.size // 4
    rgb = np.empty((n_v, 3), dtype=np.uint8)
    rgb[:, 0] = force_color[0]
    rgb[:, 1] = force_color[1]
    rgb[:, 2] = force_color[2]
    children[0]["attributes"]["color"] = rgb.flatten()


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def build_zuko(graph: Scenegraph, pipeline_name: str, parent: str = "root") -> None:
    """
    Attach the Zuko rig to ``graph`` under ``parent``.

    Must be called AFTER:
        * the pipeline is registered (so the mesh instances have a
          valid pipeline to bind to).

    The mesh primitives (``assets/cube.off``, ``assets/sphere.off``,
    ``assets/cylinder.off``) are loaded here with unique names per part
    so each body part keeps its own color buffer. The 4->3 component
    color workaround is applied to every loaded mesh.

    Default pose (T-pose-like): Zuko stands upright with arms rotated
    out (rotationZ +/- pi/2 on the shoulders) so that the arms hang
    along the local Y axis. The caller can override joint transforms
    via ``apply_zuko_pose``.
    """
    # --- 1. Cargar mallas con colores por parte ---------------------------
    graph.load_and_register_mesh(
        "zuko_torso_cube", "assets/cube.off", force_color=FIRE_RED.copy()
    )
    _strip_color_alpha(graph, "zuko_torso_cube", FIRE_RED)

    graph.load_and_register_mesh(
        "zuko_neck_cube", "assets/cube.off", force_color=SKIN.copy()
    )
    _strip_color_alpha(graph, "zuko_neck_cube", SKIN)

    graph.load_and_register_mesh(
        "zuko_head_sphere", "assets/sphere.off", force_color=SKIN.copy()
    )
    _strip_color_alpha(graph, "zuko_head_sphere", SKIN)

    # Biceps y antebrazos comparten el rojo del torso.
    graph.load_and_register_mesh(
        "zuko_arm_cube", "assets/cube.off", force_color=FIRE_RED.copy()
    )
    _strip_color_alpha(graph, "zuko_arm_cube", FIRE_RED)

    graph.load_and_register_mesh(
        "zuko_forearm_cube", "assets/cube.off", force_color=SKIN.copy()
    )
    _strip_color_alpha(graph, "zuko_forearm_cube", SKIN)

    graph.load_and_register_mesh(
        "zuko_hand_cube", "assets/cube.off", force_color=SKIN.copy()
    )
    _strip_color_alpha(graph, "zuko_hand_cube", SKIN)

    # Muslos: rojo oscuro imperial (mismo tono que el torso para uniforme).
    graph.load_and_register_mesh(
        "zuko_thigh_cube", "assets/cube.off", force_color=FIRE_RED.copy()
    )
    _strip_color_alpha(graph, "zuko_thigh_cube", FIRE_RED)

    # Pantorrillas: rojo mas oscuro (pantalones).
    graph.load_and_register_mesh(
        "zuko_shin_cube", "assets/cube.off", force_color=PANTS.copy()
    )
    _strip_color_alpha(graph, "zuko_shin_cube", PANTS)

    # Pies: gris oscuro.
    graph.load_and_register_mesh(
        "zuko_foot_cube", "assets/cube.off", force_color=BOOTS.copy()
    )
    _strip_color_alpha(graph, "zuko_foot_cube", BOOTS)

    # Espadas: cilindro delgado y largo, color acero.
    graph.load_and_register_mesh(
        "zuko_sword_cylinder", "assets/cylinder.off", force_color=STEEL.copy()
    )
    _strip_color_alpha(graph, "zuko_sword_cylinder", STEEL)

    # --- 2. zuko_root: lo posiciona en el primer plano -------------------
    graph.add_transform("zuko_root", tr.translate(*ZUKO_TRANSLATE))
    graph.add_edge(parent, "zuko_root")

    # --- 3. torso (joint raiz del personaje) -----------------------------
    graph.add_transform("torso", tr.identity())
    graph.add_edge("zuko_root", "torso")

    # --- 3a. torso_visual + torso_mesh -----------------------------------
    graph.add_transform("torso_visual", tr.scale(0.8, 1.2, 0.5))
    graph.add_edge("torso", "torso_visual")
    graph.add_mesh_instance("torso_mesh", "zuko_torso_cube", pipeline_name)
    graph.add_edge("torso_visual", "torso_mesh")

    # --- 4. cuello (joint -> visual -> mesh) -----------------------------
    graph.add_transform("cuello", tr.translate(0.0, 0.6, 0.0))
    graph.add_edge("torso", "cuello")

    graph.add_transform(
        "cuello_visual",
        tr.matmul([tr.translate(0.0, 0.1, 0.0), tr.scale(0.25, 0.2, 0.25)]),
    )
    graph.add_edge("cuello", "cuello_visual")
    graph.add_mesh_instance("cuello_mesh", "zuko_neck_cube", pipeline_name)
    graph.add_edge("cuello_visual", "cuello_mesh")

    # --- 5. cabeza (hija del cuello, sigue la cadena Programa.md) -------
    graph.add_transform("cabeza", tr.translate(0.0, 0.9, 0.0))
    graph.add_edge("torso", "cabeza")

    graph.add_transform("cabeza_visual", tr.scale(0.45, 0.62, 0.52))
    graph.add_edge("cabeza", "cabeza_visual")
    graph.add_mesh_instance("cabeza_mesh", "zuko_head_sphere", pipeline_name)
    graph.add_edge("cabeza_visual", "cabeza_mesh")

    # --- 6. brazo_der ----------------------------------------------------
    brazo_der_joint = tr.matmul([
        tr.translate(0.4, 0.55, 0.0),
        tr.rotationZ(np.pi / 2),
    ])
    graph.add_transform("brazo_der", brazo_der_joint)
    graph.add_edge("torso", "brazo_der")

    graph.add_transform(
        "brazo_der_visual",
        tr.matmul([tr.translate(0.0, -0.35, 0.0), tr.scale(0.2, 0.7, 0.2)]),
    )
    graph.add_edge("brazo_der", "brazo_der_visual")
    graph.add_mesh_instance("brazo_der_mesh", "zuko_arm_cube", pipeline_name)
    graph.add_edge("brazo_der_visual", "brazo_der_mesh")

    # --- 6a. antebrazo_der -----------------------------------------------
    graph.add_transform("antebrazo_der", tr.translate(0.0, -0.7, 0.0))
    graph.add_edge("brazo_der", "antebrazo_der")

    graph.add_transform(
        "antebrazo_der_visual",
        tr.matmul([tr.translate(0.0, -0.35, 0.0), tr.scale(0.18, 0.7, 0.18)]),
    )
    graph.add_edge("antebrazo_der", "antebrazo_der_visual")
    graph.add_mesh_instance(
        "antebrazo_der_mesh", "zuko_forearm_cube", pipeline_name
    )
    graph.add_edge("antebrazo_der_visual", "antebrazo_der_mesh")

    # --- 6b. mano_der + espada_der ---------------------------------------
    graph.add_transform("mano_der", tr.translate(0.0, -0.7, 0.0))
    graph.add_edge("antebrazo_der", "mano_der")

    graph.add_transform(
        "mano_der_visual",
        tr.matmul([tr.translate(0.0, -0.075, 0.0), tr.scale(0.2, 0.15, 0.2)]),
    )
    graph.add_edge("mano_der", "mano_der_visual")
    graph.add_mesh_instance("mano_der_mesh", "zuko_hand_cube", pipeline_name)
    graph.add_edge("mano_der_visual", "mano_der_mesh")

    # Espada: hijo de mano_der (sale hacia adelante del cuerpo).
    graph.add_transform(
        "espada_der", tr.translate(0.0, -0.3, 0.15)
    )
    graph.add_edge("mano_der", "espada_der")

    graph.add_transform("espada_der_visual", tr.scale(0.05, 0.05, 1.2))
    graph.add_edge("espada_der", "espada_der_visual")
    graph.add_mesh_instance(
        "espada_der_mesh", "zuko_sword_cylinder", pipeline_name
    )
    graph.add_edge("espada_der_visual", "espada_der_mesh")

    # --- 7. brazo_izq (espejo) ------------------------------------------
    brazo_izq_joint = tr.matmul([
        tr.translate(-0.4, 0.55, 0.0),
        tr.rotationZ(-np.pi / 2),
    ])
    graph.add_transform("brazo_izq", brazo_izq_joint)
    graph.add_edge("torso", "brazo_izq")

    graph.add_transform(
        "brazo_izq_visual",
        tr.matmul([tr.translate(0.0, -0.35, 0.0), tr.scale(0.2, 0.7, 0.2)]),
    )
    graph.add_edge("brazo_izq", "brazo_izq_visual")
    graph.add_mesh_instance("brazo_izq_mesh", "zuko_arm_cube", pipeline_name)
    graph.add_edge("brazo_izq_visual", "brazo_izq_mesh")

    # --- 7a. antebrazo_izq -----------------------------------------------
    graph.add_transform("antebrazo_izq", tr.translate(0.0, -0.7, 0.0))
    graph.add_edge("brazo_izq", "antebrazo_izq")

    graph.add_transform(
        "antebrazo_izq_visual",
        tr.matmul([tr.translate(0.0, -0.35, 0.0), tr.scale(0.18, 0.7, 0.18)]),
    )
    graph.add_edge("antebrazo_izq", "antebrazo_izq_visual")
    graph.add_mesh_instance(
        "antebrazo_izq_mesh", "zuko_forearm_cube", pipeline_name
    )
    graph.add_edge("antebrazo_izq_visual", "antebrazo_izq_mesh")

    # --- 7b. mano_izq + espada_izq ---------------------------------------
    graph.add_transform("mano_izq", tr.translate(0.0, -0.7, 0.0))
    graph.add_edge("antebrazo_izq", "mano_izq")

    graph.add_transform(
        "mano_izq_visual",
        tr.matmul([tr.translate(0.0, -0.075, 0.0), tr.scale(0.2, 0.15, 0.2)]),
    )
    graph.add_edge("mano_izq", "mano_izq_visual")
    graph.add_mesh_instance("mano_izq_mesh", "zuko_hand_cube", pipeline_name)
    graph.add_edge("mano_izq_visual", "mano_izq_mesh")

    graph.add_transform(
        "espada_izq", tr.translate(0.0, -0.3, 0.15)
    )
    graph.add_edge("mano_izq", "espada_izq")

    graph.add_transform("espada_izq_visual", tr.scale(0.05, 0.05, 1.2))
    graph.add_edge("espada_izq", "espada_izq_visual")
    graph.add_mesh_instance(
        "espada_izq_mesh", "zuko_sword_cylinder", pipeline_name
    )
    graph.add_edge("espada_izq_visual", "espada_izq_mesh")

    # --- 8. muslo_der ----------------------------------------------------
    graph.add_transform("muslo_der", tr.translate(0.2, -0.6, 0.0))
    graph.add_edge("torso", "muslo_der")

    graph.add_transform(
        "muslo_der_visual",
        tr.matmul([tr.translate(0.0, -0.425, 0.0), tr.scale(0.25, 0.85, 0.25)]),
    )
    graph.add_edge("muslo_der", "muslo_der_visual")
    graph.add_mesh_instance("muslo_der_mesh", "zuko_thigh_cube", pipeline_name)
    graph.add_edge("muslo_der_visual", "muslo_der_mesh")

    # --- 8a. pantorrilla_der ---------------------------------------------
    graph.add_transform("pantorrilla_der", tr.translate(0.0, -0.85, 0.0))
    graph.add_edge("muslo_der", "pantorrilla_der")

    graph.add_transform(
        "pantorrilla_der_visual",
        tr.matmul([tr.translate(0.0, -0.4, 0.0), tr.scale(0.2, 0.8, 0.2)]),
    )
    graph.add_edge("pantorrilla_der", "pantorrilla_der_visual")
    graph.add_mesh_instance(
        "pantorrilla_der_mesh", "zuko_shin_cube", pipeline_name
    )
    graph.add_edge("pantorrilla_der_visual", "pantorrilla_der_mesh")

    # --- 8b. pie_der -----------------------------------------------------
    graph.add_transform("pie_der", tr.translate(0.0, -0.8, 0.15))
    graph.add_edge("pantorrilla_der", "pie_der")

    graph.add_transform(
        "pie_der_visual",
        tr.matmul([tr.translate(0.0, -0.125, 0.0), tr.scale(0.3, 0.25, 0.6)]),
    )
    graph.add_edge("pie_der", "pie_der_visual")
    graph.add_mesh_instance("pie_der_mesh", "zuko_foot_cube", pipeline_name)
    graph.add_edge("pie_der_visual", "pie_der_mesh")

    # --- 9. muslo_izq (espejo) -------------------------------------------
    graph.add_transform("muslo_izq", tr.translate(-0.2, -0.6, 0.0))
    graph.add_edge("torso", "muslo_izq")

    graph.add_transform(
        "muslo_izq_visual",
        tr.matmul([tr.translate(0.0, -0.425, 0.0), tr.scale(0.25, 0.85, 0.25)]),
    )
    graph.add_edge("muslo_izq", "muslo_izq_visual")
    graph.add_mesh_instance("muslo_izq_mesh", "zuko_thigh_cube", pipeline_name)
    graph.add_edge("muslo_izq_visual", "muslo_izq_mesh")

    # --- 9a. pantorrilla_izq ---------------------------------------------
    graph.add_transform("pantorrilla_izq", tr.translate(0.0, -0.85, 0.0))
    graph.add_edge("muslo_izq", "pantorrilla_izq")

    graph.add_transform(
        "pantorrilla_izq_visual",
        tr.matmul([tr.translate(0.0, -0.4, 0.0), tr.scale(0.2, 0.8, 0.2)]),
    )
    graph.add_edge("pantorrilla_izq", "pantorrilla_izq_visual")
    graph.add_mesh_instance(
        "pantorrilla_izq_mesh", "zuko_shin_cube", pipeline_name
    )
    graph.add_edge("pantorrilla_izq_visual", "pantorrilla_izq_mesh")

    # --- 9b. pie_izq -----------------------------------------------------
    graph.add_transform("pie_izq", tr.translate(0.0, -0.8, 0.15))
    graph.add_edge("pantorrilla_izq", "pie_izq")

    graph.add_transform(
        "pie_izq_visual",
        tr.matmul([tr.translate(0.0, -0.125, 0.0), tr.scale(0.3, 0.25, 0.6)]),
    )
    graph.add_edge("pie_izq", "pie_izq_visual")
    graph.add_mesh_instance("pie_izq_mesh", "zuko_foot_cube", pipeline_name)
    graph.add_edge("pie_izq_visual", "pie_izq_mesh")

    # --- 10. Snapshot de la pose neutra para ``apply_zuko_pose`` --------
    _record_originals(graph)


def get_zuko_joints():
    """
    Return the list of joint node keys that the rest of the system can
    animate via ``apply_zuko_pose``. The neck (``cuello``) is intentionally
    omitted: the head pivots from the torso (Programa.md puts ``cabeza``
    as a child of ``torso``, not of ``cuello``, so the neck is a fixed
    visual spacer, not an articulated joint).
    """
    return [
        "torso",
        "cabeza",
        "brazo_der",
        "antebrazo_der",
        "mano_der",
        "brazo_izq",
        "antebrazo_izq",
        "mano_izq",
        "muslo_der",
        "pantorrilla_der",
        "muslo_izq",
        "pantorrilla_izq",
    ]


def apply_zuko_pose(graph: Scenegraph, pose_dict: dict) -> None:
    """
    Apply a pose to Zuko by composing the cached rest-pose transform
    with the supplied rotation for every joint in ``get_zuko_joints()``.

    For each joint:

        transform = original_transform @ pose_dict.get(joint, identity)

    A joint missing from ``pose_dict`` falls back to ``tr.identity()``,
    so its transform is restored to the rest pose captured in
    ``build_zuko``. Unknown keys in ``pose_dict`` are ignored.

    Parameters
    ----------
    graph : Scenegraph
        The scene graph that ``build_zuko`` populated.
    pose_dict : dict
        Mapping ``joint_name -> 4x4 np.ndarray``. Each value should be
        a rotation matrix (``tr.rotationX/Y/Z(theta)``) that is applied
        *after* the joint's rest pose, pivoting the joint in its local
        frame. Values do not need to include the base translation -
        that is restored from the cache.
    """
    originals = _ZUKO_ORIGINAL_TRANSFORMS.get(id(graph))
    if originals is None:
        # ``build_zuko`` was not called for this graph, or the cache
        # was cleared. Nothing meaningful to compose against.
        return

    for joint in get_zuko_joints():
        if joint not in graph.nodes:
            continue
        original = originals.get(joint)
        if original is None:
            continue
        rotation = pose_dict.get(joint, tr.identity())
        graph.nodes[joint]["transform"] = original @ np.asarray(
            rotation, dtype=np.float32
        )
