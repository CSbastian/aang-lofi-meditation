"""
Modulo de integracion de skinning para el modelo de Aang.

Carga el modelo GLTF, construye el Scenegraph de joints, crea los vertex
lists para el shader de skinning LBS, y calcula las matrices de skinning.

Patron copiado directamente de examples/skinning/__init__.py, adaptado
para el modelo de Aang (330 joints, LBS solamente).
"""

import math

import numpy as np
import pyglet.gl as GL

from grafica import transformations as tr
from grafica.gltf import GltfModel
from grafica.scenegraph import Scenegraph


# ---------------------------------------------------------------------------
# Lotus pose parameters — easy to edit
# ---------------------------------------------------------------------------

# Pelvis
PELVIS_TILT_DEG = 0          # backward tilt (degrees, Y axis)

# Left leg (full 3-axis per joint)
THIGH_L_X_DEG = 0.0              # thigh twist (X)
THIGH_L_Y_DEG = -120.5            # hip flexion (Y, negative = knee up)
THIGH_L_Z_DEG = 34.4             # hip abduction (Z, positive = open)
CALF_L_X_DEG = 120.0               # calf twist (X)
CALF_L_Y_DEG = 120.0              # knee bend (Y)
CALF_L_Z_DEG = 0.0               # calf sideways (Z)
FOOT_L_X_DEG = 90.0               # foot twist (X)
FOOT_L_Y_DEG = 0.0             # foot up/down (Y)
FOOT_L_Z_DEG = -62.9             # foot rotation (Z)

# Right leg (full 3-axis per joint)
THIGH_R_X_DEG = 0.0
THIGH_R_Y_DEG = -120.5
THIGH_R_Z_DEG = 34.4            # (sign inverted for symmetry)
CALF_R_X_DEG = 120.0
CALF_R_Y_DEG = 120.0
CALF_R_Z_DEG = 10.0
FOOT_R_X_DEG = 90.0
FOOT_R_Y_DEG = 17.2
FOOT_R_Z_DEG = -62.9              # (sign inverted for symmetry)

# Left arm (full 3-axis per joint)
CLAVICLE_L_X_DEG = 0.0           # clavicle twist (X)
CLAVICLE_L_Y_DEG = 0.0         # shoulder drop (Y)
CLAVICLE_L_Z_DEG = 0.0           # clavicle forward (Z)

UPPERARM_L_X_DEG = 35.0          # arm twist (X)
UPPERARM_L_Y_DEG = 10.0         # arm rotation (Y)
UPPERARM_L_Z_DEG = -20.6          # arm forward (Z)

LOWERARM_L_X_DEG = -65.0           # forearm twist (X)
LOWERARM_L_Y_DEG = 70.8         # elbow bend (Y)
LOWERARM_L_Z_DEG = -39.0           # forearm sideways (Z)

HAND_L_X_DEG = 0.0               # hand twist (X)
HAND_L_Y_DEG = 11.5              # hand rotation (Y)
HAND_L_Z_DEG = -11.5             # hand tilt (Z)

# Right arm (full 3-axis per joint)
CLAVICLE_R_X_DEG = 0.0
CLAVICLE_R_Y_DEG = 0.0
CLAVICLE_R_Z_DEG = 0.0

UPPERARM_R_X_DEG = 35.0
UPPERARM_R_Y_DEG = 10.0
UPPERARM_R_Z_DEG = -20.6

LOWERARM_R_X_DEG = -65.0
LOWERARM_R_Y_DEG = 70.8
LOWERARM_R_Z_DEG = -39.0

HAND_R_X_DEG = 0.0
HAND_R_Y_DEG = 11.5
HAND_R_Z_DEG = 11.5

# Head
HEAD_X_DEG = 0.0                # head nod (X, positive = look up)
HEAD_Y_DEG = 0.0                # head turn (Y, positive = look right)
HEAD_Z_DEG = 0.0                # head tilt (Z, positive = tilt right)

# Hand closure (0 = open, 90 = fist)
HAND_CLOSURE_DEG = 0
EYE_CLOSURE_DEG = 56.0

# Breathing animation
BREATH_AMPLITUDE_DEG = 1.15      # spine rotation amplitude
BREATH_FREQ_HZ = 0.5             # breaths per second (0.5 = 2-sec cycle)
WIND_AMPLITUDE_DEG = 4.6         # cape wind amplitude
WIND_FREQ_HZ = 0.3               # wind frequency
WIND_PHASE_OFFSET = 0.8          # phase offset between cape joints
HEAD_TILT_STATIC_DEG = -5.7      # static head tilt in breathing anim (X axis)


def gather_skinned_primitives_data(model):
    """
    Recolecta cada primitiva skinneada como un dict independiente, conservando
    su material para que el renderer pueda atar la textura correcta.
    """
    primitives_data = []
    for mesh_index, primitives in enumerate(model.meshes):
        for primitive_index, primitive in enumerate(primitives):
            if primitive.joints is None:
                continue
            n = primitive.positions.shape[0]
            normals = (
                primitive.normals.astype(np.float32)
                if primitive.normals is not None
                else np.zeros((n, 3), dtype=np.float32)
            )
            uvs = (
                primitive.uvs.astype(np.float32)
                if primitive.uvs is not None
                else np.zeros((n, 2), dtype=np.float32)
            )
            colors = (
                primitive.colors.astype(np.float32)
                if primitive.colors is not None
                else np.ones((n, 4), dtype=np.float32)
            )
            indices = (
                primitive.indices.astype(np.uint32)
                if primitive.indices is not None
                else np.arange(n, dtype=np.uint32)
            )
            primitives_data.append({
                "positions": primitive.positions.astype(np.float32),
                "normals": normals,
                "uvs": uvs,
                "colors": colors,
                "joints": primitive.joints.astype(np.float32),
                "weights": primitive.weights.astype(np.float32),
                "indices": indices,
                "material_index": primitive.material_index,
            })
    return primitives_data


def setup_aang(model_path, skinning_pipeline):
    """
    Carga el modelo GLTF de Aang, construye el Scenegraph con la jerarquia
    de nodos, recolecta las primitivas skinneadas y crea los vertex lists
    para el shader de skinning LBS.

    Retorna un dict con toda la informacion necesaria para renderizar y
    animar el modelo.
    """
    model = GltfModel(model_path)

    # Encontrar el skin que la malla usa
    mesh_skin = None
    for node in model.nodes:
        if node.skin_index is not None:
            mesh_skin = model.skins[node.skin_index]
            break
    assert mesh_skin is not None, "no se encontro skin en el modelo"
    n_joints = len(mesh_skin.joints)
    print(f"[aang] joints={n_joints}")
    assert n_joints == 330, f"se esperaban 330 joints, se obtuvieron {n_joints}"

    # Construir Scenegraph con la jerarquia de nodos del GLTF
    graph = Scenegraph("root")
    node_to_scenegraph_name = []
    for node in model.nodes:
        name = f"gltf_node_{node.index}"
        graph.add_transform(name, node.local_matrix())
        node_to_scenegraph_name.append(name)
    for node in model.nodes:
        for child_idx in node.children:
            graph.add_edge(node_to_scenegraph_name[node.index], node_to_scenegraph_name[child_idx])
    for root_idx in model.scene_roots:
        graph.add_edge("root", node_to_scenegraph_name[root_idx])

    # Recolectar primitivas skinneadas
    primitives = gather_skinned_primitives_data(model)

    # Crear vertex lists para el shader de skinning
    for prim in primitives:
        n = prim["positions"].shape[0]
        vl = skinning_pipeline.vertex_list_indexed(n, GL.GL_TRIANGLES, prim["indices"].tolist())
        vl.position[:] = prim["positions"].flatten()
        vl.normal[:] = prim["normals"].flatten()
        vl.uv[:] = prim["uvs"].flatten()
        vl.joints[:] = prim["joints"].flatten()
        vl.weights[:] = prim["weights"].flatten()
        prim["vertex_list"] = vl

    # Guardar transforms base para animacion (Task 9 usara estos)
    base_transforms = {}
    for node in model.nodes:
        name = node_to_scenegraph_name[node.index]
        base_transforms[name] = node.local_matrix().copy()

    return {
        "model": model,
        "graph": graph,
        "primitives": primitives,
        "node_to_scenegraph_name": node_to_scenegraph_name,
        "n_joints": n_joints,
        "skin": mesh_skin,
        "base_transforms": base_transforms,
    }


def apply_breathing_and_wind(aang_data, time, first_call=False):
    """
    Aplica animacion procedural a la jerarquia de joints de Aang:
    - Respiracion: rotacion sinusoidal sutil en la espina (eje X)
    - Viento de la capa: rotacion ondulante en las joints de la capa
    - Inclinacion de la cabeza: rotacion fija hacia abajo (solo primer call)

    Cada frame sobreescribe los transforms desde base_transforms, asi que
    NO hay acumulacion: las oscilaciones vuelven al origen en cada llamada.

    Args:
        aang_data: dict retornado por setup_aang()
        time: tiempo de animacion actual en segundos
        first_call: si True, aplica la inclinacion estatica de la cabeza
    """
    graph = aang_data["graph"]
    base_transforms = aang_data["base_transforms"]
    n2s = aang_data["node_to_scenegraph_name"]

    # Respiracion: joints de la espina rotan suavemente en X
    # Indices 8..12 mapean a la cadena de la espina en el GLTF
    breath_amplitude = math.radians(BREATH_AMPLITUDE_DEG)
    breath_freq = BREATH_FREQ_HZ
    breath = breath_amplitude * math.sin(2 * math.pi * breath_freq * time)

    spine_indices = [8, 9, 10, 11, 12]
    for idx in spine_indices:
        if idx >= len(n2s):
            continue
        node_name = n2s[idx]
        if node_name not in base_transforms:
            continue
        base = base_transforms[node_name]
        graph.nodes[node_name]["transform"] = base @ tr.rotationX(breath)

    # Viento de la capa: cada joint de la capa tiene fase propia para
    # generar efecto de onda. Rotacion en Z (planeo lateral del pano).
    wind_amplitude = math.radians(WIND_AMPLITUDE_DEG)
    wind_freq = WIND_FREQ_HZ

    cape_indices = [14, 15, 16, 17]
    for i, idx in enumerate(cape_indices):
        if idx >= len(n2s):
            continue
        node_name = n2s[idx]
        if node_name not in base_transforms:
            continue
        base = base_transforms[node_name]
        phase_offset = i * WIND_PHASE_OFFSET
        wind = wind_amplitude * math.sin(2 * math.pi * wind_freq * time + phase_offset)
        graph.nodes[node_name]["transform"] = base @ tr.rotationZ(wind)

    # Inclinacion de la cabeza: rotacion fija hacia abajo (~6 grados).
    # Solo se aplica en la primera llamada; en frames siguientes la
    # respiracion/espalda se sobreescriben pero la cabeza queda fija
    # porque su transform no se toca en el bucle de arriba.
    if first_call:
        head_idx = 20
        if head_idx < len(n2s):
            node_name = n2s[head_idx]
            if node_name in base_transforms:
                base = base_transforms[node_name]
                head_tilt = tr.rotationX(math.radians(HEAD_TILT_STATIC_DEG))
                graph.nodes[node_name]["transform"] = base @ head_tilt


def compute_skin_matrices(aang_data):
    """
    Calcula las matrices de skinning para cada joint. Cada matriz es el
    producto entre la transformada global actual del joint y su inverse
    bind matrix.

    Retorna (skin_matrices, real_quats, dual_quats) donde skin_matrices es
    un array (N, 4, 4) row-major. real_quats y dual_quats son placeholders
    en cero (LBS no los usa, pero se mantienen por compatibilidad).
    """
    model = aang_data["model"]
    graph = aang_data["graph"]
    node_to_scenegraph_name = aang_data["node_to_scenegraph_name"]
    skin = aang_data["skin"]

    graph.calculate_global_transforms()

    n_joints = len(skin.joints)
    skin_matrices = np.empty((n_joints, 4, 4), dtype=np.float32)
    real_quats = np.zeros((n_joints, 4), dtype=np.float32)
    dual_quats = np.zeros((n_joints, 4), dtype=np.float32)

    for joint_index, joint_node_index in enumerate(skin.joints):
        joint_global = graph.global_transforms[node_to_scenegraph_name[joint_node_index]]
        skin_matrix = joint_global @ skin.inverse_bind_matrices[joint_index]
        skin_matrices[joint_index] = skin_matrix

    return skin_matrices, real_quats, dual_quats


def compute_aang_bbox(aang_data):
    """
    Calcula la AABB del modelo en pose actual aplicando skinning en CPU.
    Solo se usa una vez al inicio para encuadrar la camara.

    Retorna (min_pt, max_pt) como arrays np.float32 de 3 elementos.
    """
    skin_matrices, _, _ = compute_skin_matrices(aang_data)
    primitives_data = aang_data["primitives"]

    min_pt = np.array([np.inf, np.inf, np.inf], dtype=np.float32)
    max_pt = np.array([-np.inf, -np.inf, -np.inf], dtype=np.float32)
    for prim in primitives_data:
        positions = prim["positions"]
        joints = prim["joints"]
        weights = prim["weights"]
        ones = np.ones((positions.shape[0], 1), dtype=np.float32)
        homogeneous = np.hstack([positions, ones])
        skinned = np.zeros_like(homogeneous)
        for influence_index in range(4):
            joint_indices = joints[:, influence_index].astype(int)
            w = weights[:, influence_index][:, None]
            per_vertex_matrices = skin_matrices[joint_indices]
            contributions = np.einsum("nij,nj->ni", per_vertex_matrices, homogeneous)
            skinned += w * contributions
        world_positions = skinned[:, :3]
        min_pt = np.minimum(min_pt, world_positions.min(axis=0))
        max_pt = np.maximum(max_pt, world_positions.max(axis=0))
    return min_pt, max_pt


def apply_lotus_pose(aang_data, pelvis_sink=0.85, facing_deg=180):
    """
    Modifica los transforms del grafo de Aang para adoptar la postura de loto
    (sentado, piernas flectadas, manos juntas en Dhyana Mudra).

    Args:
        aang_data: dict from setup_aang()
        pelvis_sink: how much the pelvis drops (model units, positive = down)
        facing_deg: rotation around vertical axis to face the camera
    """
    graph = aang_data["graph"]
    base = aang_data["base_transforms"]
    n2s = aang_data["node_to_scenegraph_name"]
    
    # ----------------------------------------------------------------
    # 0. Rotar el personaje completo para que enfrente a la camara
    #    La camara esta en +Z, asi que rotamos 180° en Y.
    #    Object_4 (nodo 4) es la raiz del personaje.
    # ----------------------------------------------------------------
    root_name = n2s[4]
    if root_name in base:
        T_base = base[root_name]
        graph.nodes[root_name]["transform"] = T_base @ tr.rotationX(math.radians(facing_deg))

    # ----------------------------------------------------------------
    # 1. Bajar la pelvis para que Aang quede sentado en el suelo
    #    El pelvis esta en X ~+0.93 sobre el origen. Lo bajamos ~0.8.
    #    Ademas rotamos Y para inclinar la pelvis hacia atras.
    # ----------------------------------------------------------------
    pelvis_name = n2s[7]
    if pelvis_name in base:
        T_base = base[pelvis_name]
        # Bajar y rotar pelvis para sentarse
        graph.nodes[pelvis_name]["transform"] = T_base @ tr.translate(-pelvis_sink, 0.0, 0.0) @ tr.rotationY(math.radians(PELVIS_TILT_DEG))

    # ----------------------------------------------------------------
    # 2. Pierna izquierda: lotus (3-axis)
    # ----------------------------------------------------------------
    thigh_l_name = n2s[256]
    if thigh_l_name in base:
        T_base = base[thigh_l_name]
        graph.nodes[thigh_l_name]["transform"] = T_base @ tr.rotationX(math.radians(THIGH_L_X_DEG)) @ tr.rotationY(math.radians(THIGH_L_Y_DEG)) @ tr.rotationZ(math.radians(THIGH_L_Z_DEG))

    calf_l_name = n2s[257]
    if calf_l_name in base:
        T_base = base[calf_l_name]
        graph.nodes[calf_l_name]["transform"] = T_base @ tr.rotationX(math.radians(CALF_L_X_DEG)) @ tr.rotationY(math.radians(CALF_L_Y_DEG)) @ tr.rotationZ(math.radians(CALF_L_Z_DEG))

    foot_l_name = n2s[258]
    if foot_l_name in base:
        T_base = base[foot_l_name]
        graph.nodes[foot_l_name]["transform"] = T_base @ tr.rotationX(math.radians(FOOT_L_X_DEG)) @ tr.rotationY(math.radians(FOOT_L_Y_DEG)) @ tr.rotationZ(math.radians(FOOT_L_Z_DEG))

    # ----------------------------------------------------------------
    # 3. Pierna derecha: lotus (3-axis)
    # ----------------------------------------------------------------
    thigh_r_name = n2s[278]
    if thigh_r_name in base:
        T_base = base[thigh_r_name]
        graph.nodes[thigh_r_name]["transform"] = T_base @ tr.rotationX(math.radians(THIGH_R_X_DEG)) @ tr.rotationY(math.radians(THIGH_R_Y_DEG)) @ tr.rotationZ(math.radians(THIGH_R_Z_DEG))

    calf_r_name = n2s[279]
    if calf_r_name in base:
        T_base = base[calf_r_name]
        graph.nodes[calf_r_name]["transform"] = T_base @ tr.rotationX(math.radians(CALF_R_X_DEG)) @ tr.rotationY(math.radians(CALF_R_Y_DEG)) @ tr.rotationZ(math.radians(CALF_R_Z_DEG))

    foot_r_name = n2s[280]
    if foot_r_name in base:
        T_base = base[foot_r_name]
        graph.nodes[foot_r_name]["transform"] = T_base @ tr.rotationX(math.radians(FOOT_R_X_DEG)) @ tr.rotationY(math.radians(FOOT_R_Y_DEG)) @ tr.rotationZ(math.radians(FOOT_R_Z_DEG))

    # ----------------------------------------------------------------
    # 4. Brazo izquierdo
    # ----------------------------------------------------------------
    for labels, indices in [
        (("CLAVICLE_L", CLAVICLE_L_X_DEG, CLAVICLE_L_Y_DEG, CLAVICLE_L_Z_DEG), 88),
        (("UPPERARM_L", UPPERARM_L_X_DEG, UPPERARM_L_Y_DEG, UPPERARM_L_Z_DEG), 89),
        (("LOWERARM_L", LOWERARM_L_X_DEG, LOWERARM_L_Y_DEG, LOWERARM_L_Z_DEG), 90),
        (("HAND_L",     HAND_L_X_DEG,     HAND_L_Y_DEG,     HAND_L_Z_DEG), 91),
    ]:
        name = n2s[indices]
        if name in base:
            T_base = base[name]
            _x, _y, _z = labels[1], labels[2], labels[3]
            graph.nodes[name]["transform"] = (
                T_base
                @ tr.rotationX(math.radians(_x))
                @ tr.rotationY(math.radians(_y))
                @ tr.rotationZ(math.radians(_z))
            )

    # ----------------------------------------------------------------
    # 5. Brazo derecho
    # ----------------------------------------------------------------
    for labels, indices in [
        (("CLAVICLE_R", CLAVICLE_R_X_DEG, CLAVICLE_R_Y_DEG, CLAVICLE_R_Z_DEG), 156),
        (("UPPERARM_R", UPPERARM_R_X_DEG, UPPERARM_R_Y_DEG, UPPERARM_R_Z_DEG), 157),
        (("LOWERARM_R", LOWERARM_R_X_DEG, LOWERARM_R_Y_DEG, LOWERARM_R_Z_DEG), 158),
        (("HAND_R",     HAND_R_X_DEG,     HAND_R_Y_DEG,     HAND_R_Z_DEG), 159),
    ]:
        name = n2s[indices]
        if name in base:
            T_base = base[name]
            _x, _y, _z = labels[1], labels[2], labels[3]
            graph.nodes[name]["transform"] = (
                T_base
                @ tr.rotationX(math.radians(_x))
                @ tr.rotationY(math.radians(_y))
                @ tr.rotationZ(math.radians(_z))
            )

    # ----------------------------------------------------------------
    # 6. Cabeza: inclinacion hacia abajo (mirada meditativa)
    # ----------------------------------------------------------------
    head_name = n2s[20]
    if head_name in base:
        T_base = base[head_name]
        graph.nodes[head_name]["transform"] = (
            T_base
            @ tr.rotationX(math.radians(HEAD_X_DEG))
            @ tr.rotationY(math.radians(HEAD_Y_DEG))
            @ tr.rotationZ(math.radians(HEAD_Z_DEG))
        )

    # ----------------------------------------------------------------
    # 7. Cerrar manos (fist): aplica curl progresivo a los dedos
    #    Segmentos _01 (knuckle) curl parcial, _02 (mid) mas, _03 (tip) total
    # ----------------------------------------------------------------
    if HAND_CLOSURE_DEG != 0.0:
        # Indice de cada segmento del dedo: (nombre, multiplicador de curl)
        # Izq = indices en n2s, Der = indices en n2s
        # Para el pulgar (thumb) los indices son seguidos
        # Para otros dedos hay un metacarpal en el medio
        finger_segments = [
            # (idx, curl_factor)  -- metacarpal: 0.25, knuckle: 0.5, mid: 0.75, tip: 1.0
            # Left thumb: metacarpal(91 children: 92=thumb_01), 93, 94
            (92, 0.5), (93, 0.75), (94, 1.0),
            # Left index: metacarpal 96, 97, 98, 99
            (96, 0.25), (97, 0.5), (98, 0.75), (99, 1.0),
            # Left middle: metacarpal 101, 102, 103, 104
            (101, 0.25), (102, 0.5), (103, 0.75), (104, 1.0),
            # Left ring: metacarpal 106, 107, 108, 109
            (106, 0.25), (107, 0.5), (108, 0.75), (109, 1.0),
            # Left pinky: metacarpal 111, 112, 113, 114
            (111, 0.25), (112, 0.5), (113, 0.75), (114, 1.0),
            # Right thumb: 160, 161, 162
            (160, 0.5), (161, 0.75), (162, 1.0),
            # Right index: metacarpal 164, 165, 166, 167
            (164, 0.25), (165, 0.5), (166, 0.75), (167, 1.0),
            # Right middle: metacarpal 169, 170, 171, 172
            (169, 0.25), (170, 0.5), (171, 0.75), (172, 1.0),
            # Right ring: metacarpal 174, 175, 176, 177
            (174, 0.25), (175, 0.5), (176, 0.75), (177, 1.0),
            # Right pinky: metacarpal 179, 180, 181, 182
            (179, 0.25), (180, 0.5), (181, 0.75), (182, 1.0),
        ]
        for idx, curl_factor in finger_segments:
            if idx < len(n2s):
                node_name = n2s[idx]
                if node_name in base:
                    T_base = base[node_name]
                    angle = HAND_CLOSURE_DEG * curl_factor
                    graph.nodes[node_name]["transform"] = (
                        T_base @ tr.rotationZ(math.radians(angle))
                    )

    # ----------------------------------------------------------------
    # 8. Cerrar ojos: upper lid baja, lower lid sube
    #    Para cerrar, el upper lid rota negativo y el lower positivo
    # ----------------------------------------------------------------
    if EYE_CLOSURE_DEG != 0.0:
        # (idx, direction): -1 = upper lid (baja), +1 = lower lid (sube)
        eye_lids = [
            (48, -1),  # L_eye_lid_upper_mid_032
            (46,  1),  # L_eye_lid_lower_mid_031
            (63, -1),  # R_eye_lid_upper_mid_040
            (61,  1),  # R_eye_lid_lower_mid_039
        ]
        for idx, direction in eye_lids:
            if idx < len(n2s):
                node_name = n2s[idx]
                if node_name in base:
                    T_base = base[node_name]
                    angle = EYE_CLOSURE_DEG * direction
                    graph.nodes[node_name]["transform"] = (
                        T_base @ tr.rotationX(math.radians(angle))
                    )
