"""
Scene builder for the Aang Lo-Fi meditation scene.

Loads static GLTF assets, creates vertex lists with the Phong pipeline,
composes the scene with placement transforms, and provides lighting/fog
configuration helpers.
"""

import math
from pathlib import Path

import numpy as np
from OpenGL import GL
from PIL import Image
from pyglet.gl import GL_REPEAT

from grafica.gltf import GltfModel
from grafica.textures import texture_2D_setup
import grafica.transformations as tr

ASSETS_DIR = Path(__file__).parent / "assets"


# ---------------------------------------------------------------------------
# Lighting / fog configuration
# ---------------------------------------------------------------------------

def get_lighting_config():
    """Return a dict with all lighting, fog, and background parameters.

    Ajustado para escena nocturna Lo-Fi: ambiente bajo, especular reducida
    al 10% y luz lunar calida. Valores basados en tablas de Phong (Jade=12.8,
    Black Plastic=32, Obsidian=38.4) y la regla k_a + k_d + k_s ~ 1.
    """
    return {
        "light_direction": np.array([0.4, 0.7, 0.5], dtype=np.float32),
        "light_color": np.array([0.95, 0.88, 0.70], dtype=np.float32),
        "ambient_strength": 0.18,
        "shininess": 16.0,
        "specular_strength": 0.10,
        "fog_color": np.array([0.15, 0.18, 0.30, 1.0], dtype=np.float32),
        "fog_near": 10.0,
        "fog_far": 30.0,
        "background_bottom": (0.15, 0.35, 0.65),
        "background_top": (0.35, 0.55, 0.85),
    }


def setup_lighting(pipeline, config, camera_position):
    """Set all lighting and fog uniforms on *pipeline* using *config*."""
    pipeline.use()

    # vec3 uniforms — column-major reshape
    pipeline["light_direction"] = config["light_direction"].reshape(3, 1, order="F")
    pipeline["light_color"] = config["light_color"].reshape(3, 1, order="F")
    pipeline["camera_position"] = np.array(camera_position, dtype=np.float32).reshape(3, 1, order="F")

    # scalar uniforms
    pipeline["ambient_strength"] = config["ambient_strength"]
    pipeline["shininess"] = config["shininess"]
    pipeline["specular_strength"] = config.get("specular_strength", 1.0)

    # fog uniforms
    pipeline["fog_color"] = config["fog_color"].reshape(4, 1, order="F")
    pipeline["fog_near"] = config["fog_near"]
    pipeline["fog_far"] = config["fog_far"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_white_texture():
    """Create a 1x1 white pixel texture as fallback for untextured materials."""
    return texture_2D_setup(Image.new("RGB", (1, 1), color=(255, 255, 255)))


def _make_vertex_list(pipeline, primitive):
    """Create a vertex list for one GLTF primitive on *pipeline*.

    Fills position, normal, and uv attributes.  Returns the pyglet
    VertexList (or VertexDomainIndexed) object.
    """
    positions = primitive.positions
    n_verts = positions.shape[0]
    indices = primitive.indices.tolist() if primitive.indices is not None else list(range(n_verts))

    vl = pipeline.vertex_list_indexed(n_verts, GL.GL_TRIANGLES, indices)

    vl.position[:] = positions.flatten()

    if primitive.normals is not None:
        vl.normal[:] = primitive.normals.flatten()
    else:
        # flat default normals pointing up
        default_normals = np.tile([0.0, 1.0, 0.0], (n_verts, 1)).astype(np.float32)
        vl.normal[:] = default_normals.flatten()

    if primitive.uvs is not None:
        vl.uv[:] = primitive.uvs.flatten()
    else:
        vl.uv[:] = np.zeros(n_verts * 2, dtype=np.float32)

    return vl


def _resolve_texture(model, material_index, white_texture):
    """Return the GL texture ID for a material, falling back to white."""
    if material_index is None:
        return white_texture
    material = model.materials[material_index]
    tex_idx = material.get("base_color_texture")
    if tex_idx is not None and model.texture_gl_ids and tex_idx < len(model.texture_gl_ids):
        gl_id = model.texture_gl_ids[tex_idx]
        if gl_id is not None:
            return gl_id
    return white_texture


def _is_transparent_material(model, material_index):
    """Heuristic: materials with alpha < 1 in base_color_factor are transparent."""
    if material_index is None:
        return False
    material = model.materials[material_index]
    bcf = material.get("base_color_factor")
    if bcf is not None and len(bcf) == 4 and bcf[3] < 0.99:
        return True
    return False


def _load_asset(pipeline, asset_name, white_texture, max_meshes=None, mesh_indices=None):
    """Load a GLTF asset and return a list of primitive dicts.

    Each dict: {"vertex_list", "texture_id", "is_transparent", "material_index"}
    The model is discarded after extraction to free memory.

    Args:
        mesh_indices: optional list of mesh indices to load (e.g. [0,1,2,3,7,8,9] for a complete tree).
            If None, uses max_meshes to limit, or loads all.
    """
    asset_path = ASSETS_DIR / asset_name / "scene.gltf"
    if not asset_path.exists():
        print(f"[scene_builder] WARNING: asset not found: {asset_path}")
        return []

    model = GltfModel(str(asset_path))
    model.upload_textures()

    primitives = []
    if mesh_indices is not None:
        mesh_iter = [model.meshes[i] for i in mesh_indices if i < len(model.meshes)]
    else:
        mesh_limit = max_meshes if max_meshes is not None else len(model.meshes)
        mesh_iter = model.meshes[:mesh_limit]
    for mesh_prims in mesh_iter:
        for prim in mesh_prims:
            vl = _make_vertex_list(pipeline, prim)
            tex_id = _resolve_texture(model, prim.material_index, white_texture)
            transparent = _is_transparent_material(model, prim.material_index)
            # Extract base color factor from material (for untextured meshes like axis)
            bcf = None
            if prim.material_index is not None and prim.material_index < len(model.materials):
                mat = model.materials[prim.material_index]
                bcf = mat.get("base_color_factor", None)
            primitives.append({
                "vertex_list": vl,
                "texture_id": tex_id,
                "is_transparent": transparent,
                "material_index": prim.material_index,
                "base_color_factor": bcf,
            })

    # free the model data (textures stay on GPU via GL IDs)
    del model
    return primitives


def _load_forest_tree_templates(pipeline, white_texture, mesh_indices, asset_name="forest",
                                 gltf_filename="scene.gltf"):
    """Carga los meshes de un asset GLTF y devuelve una lista de tuplas
    (primitives, baked_min_y, baked_center_xz), una entrada por mesh.

    Args:
        asset_name: nombre de la carpeta dentro de assets/ (ej: 'forest',
            'mossy_rock').
        gltf_filename: nombre del archivo .gltf (default 'scene.gltf').
            El asset grass usa 'sketch.gltf' en su lugar.

    baked_min_y: coord Y minima del mesh en espacio baked (para apoyar en suelo)
    baked_center_xz: tupla (cx, cz) del centro visual en espacio baked
        (para compensar el offset y que el mesh quede donde se le pide)
    """
    asset_path = ASSETS_DIR / asset_name / gltf_filename
    if not asset_path.exists():
        print(f"[scene_builder] WARNING: asset not found: {asset_path}")
        return []

    model = GltfModel(str(asset_path))
    model.upload_textures()

    templates = []
    for mi in mesh_indices:
        if mi >= len(model.meshes):
            continue
        mesh_prims = model.meshes[mi]
        if not mesh_prims:
            continue
        prims = []
        baked_min_y = float("inf")
        baked_cx = baked_cz = 0.0
        baked_n = 0
        for prim in mesh_prims:
            vl = _make_vertex_list(pipeline, prim)
            tex_id = _resolve_texture(model, prim.material_index, white_texture)
            transparent = _is_transparent_material(model, prim.material_index)
            bcf = None
            if prim.material_index is not None and prim.material_index < len(model.materials):
                mat = model.materials[prim.material_index]
                bcf = mat.get("base_color_factor", None)
            prims.append({
                "vertex_list": vl,
                "texture_id": tex_id,
                "is_transparent": transparent,
                "material_index": prim.material_index,
                "base_color_factor": bcf,
            })
            if prim.positions is not None and prim.positions.size > 0:
                pos = prim.positions
                baked_min_y = min(baked_min_y, float(pos[:, 1].min()))
                baked_cx += float(pos[:, 0].mean())
                baked_cz += float(pos[:, 2].mean())
                baked_n += 1
        if not prims:
            continue
        if baked_min_y == float("inf"):
            baked_min_y = 0.0
        if baked_n > 0:
            baked_cx /= baked_n
            baked_cz /= baked_n
        templates.append((prims, baked_min_y, (baked_cx, baked_cz)))

    del model
    return templates


def _load_bush_templates(pipeline, white_texture):
    """Carga la unica mesh del asset arbusto y devuelve la tupla
    (primitives, baked_min_y). Ver _load_forest_tree_templates para el
    contrato de baked_min_y.
    """
    asset_path = ASSETS_DIR / "arbusto" / "scene.gltf"
    if not asset_path.exists():
        print(f"[scene_builder] WARNING: arbusto asset not found: {asset_path}")
        return None

    model = GltfModel(str(asset_path))
    model.upload_textures()

    prims = []
    baked_min_y = float("inf")
    for mesh_prims in model.meshes:
        for prim in mesh_prims:
            vl = _make_vertex_list(pipeline, prim)
            tex_id = _resolve_texture(model, prim.material_index, white_texture)
            transparent = _is_transparent_material(model, prim.material_index)
            bcf = None
            if prim.material_index is not None and prim.material_index < len(model.materials):
                mat = model.materials[prim.material_index]
                bcf = mat.get("base_color_factor", None)
            prims.append({
                "vertex_list": vl,
                "texture_id": tex_id,
                "is_transparent": transparent,
                "material_index": prim.material_index,
                "base_color_factor": bcf,
            })
            if prim.positions is not None and prim.positions.size > 0:
                baked_min_y = min(baked_min_y, float(prim.positions[:, 1].min()))

    if not prims:
        del model
        return None
    if baked_min_y == float("inf"):
        baked_min_y = 0.0

    del model
    return (prims, baked_min_y)


def _make_circle_floor(pipeline, radius, segments=64):
    """Genera un piso circular como un triangle fan.

    Args:
        pipeline: Phong pipeline para crear el vertex list
        radius: radio del circulo en unidades de mundo
        segments: numero de segmentos del circulo (mas = mas suave)

    Returns:
        Lista con un solo dict de primitiva (vertex_list, texture_id, etc)
    """
    # Vertices: centro + perimetro
    n_vertices = 1 + segments
    positions = np.zeros((n_vertices, 3), dtype=np.float32)
    normals = np.zeros((n_vertices, 3), dtype=np.float32)
    uvs = np.zeros((n_vertices, 2), dtype=np.float32)

    # Centro del circulo
    positions[0] = [0.0, 0.0, 0.0]
    normals[0] = [0.0, 1.0, 0.0]
    uvs[0] = [0.5, 0.5]

    # Perimetro del circulo
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        positions[i + 1] = [x, 0.0, z]
        normals[i + 1] = [0.0, 1.0, 0.0]
        # UVs: mapear de (0,0) a (1,1) en el circulo
        uvs[i + 1] = [0.5 + 0.5 * math.cos(angle), 0.5 + 0.5 * math.sin(angle)]

    # Indices: triangle fan desde el centro (CCW visto desde arriba = +Y)
    indices = []
    for i in range(segments):
        indices.extend([0, (i + 1) % segments + 1, i + 1])

    vl = pipeline.vertex_list_indexed(n_vertices, GL.GL_TRIANGLES, indices)
    vl.position[:] = positions.flatten()
    vl.normal[:] = normals.flatten()
    vl.uv[:] = uvs.flatten()

    return [{
        "vertex_list": vl,
        "texture_id": None,  # Se asigna despues
        "is_transparent": False,
        "material_index": None,
        "base_color_factor": None,
    }]


def _scatter_forest_group(pipeline, white_tex, mesh_indices, count, inner_r, outer_r,
                          scale_min, scale_max, seed, cx, cz, all_primitives,
                          asset_name="forest", gltf_filename="scene.gltf",
                          rx_deg=0.0):
    """Carga un grupo de meshes y los esparce en un anillo alrededor de (cx,cz).

    rx_deg: rotacion extra en X (en grados) aplicada despues de la rotacion
        Y aleatoria. Util para "acostar" meshes que vienen parados (ej:
        pasto -> rotar 90 para que quede plano en el suelo).
    """
    templates = _load_forest_tree_templates(pipeline, white_tex, mesh_indices,
                                            asset_name, gltf_filename)
    if not templates:
        return
    rng = np.random.default_rng(seed)
    for _ in range(count):
        angle = rng.uniform(0.0, 2.0 * math.pi)
        r = rng.uniform(inner_r, outer_r)
        tx = cx + r * math.cos(angle)
        tz = cz + r * math.sin(angle)
        s = rng.uniform(scale_min, scale_max)
        ry = rng.uniform(0.0, 2.0 * math.pi)
        prims, baked_min_y, (bcx, bcz) = templates[rng.integers(0, len(templates))]
        # Composicion: centrar en baked space, escalar, rotar Y, rotar X, colocar.
        # Esto asegura que el centro visual queda en (tx, tz) sin importar ry.
        rx = tr.rotationX(math.radians(rx_deg)) if rx_deg != 0.0 else tr.identity()
        t = (
            tr.translate(tx, 0.0, tz)
            @ rx
            @ tr.rotationY(ry)
            @ tr.scale(s, s, s)
            @ tr.translate(-bcx, -baked_min_y, -bcz)
        )
        all_primitives.extend(_instantiate(prims, t))


def _placement(tx, ty, tz, sx=1.0, sy=1.0, sz=1.0, ry=0.0, rx=0.0, rz=0.0):
    """Build a TRS placement matrix: translate * rotateX * rotateY * rotateZ * scale."""
    T = tr.translate(tx, ty, tz)
    Rx = tr.rotationX(rx) if rx != 0.0 else tr.identity()
    Ry = tr.rotationY(ry) if ry != 0.0 else tr.identity()
    Rz = tr.rotationZ(rz) if rz != 0.0 else tr.identity()
    S = tr.scale(sx, sy, sz)
    return tr.matmul([T, Rx, Ry, Rz, S])


def _instantiate(primitives_template, transform, base_color_override=None):
    """Create scene instances from a template list of primitives.

    Each instance shares the same vertex_list but gets its own transform.
    Returns list of scene-ready primitive dicts.
    """
    instances = []
    for prim in primitives_template:
        entry = {
            "vertex_list": prim["vertex_list"],
            "transform": transform,
            "texture_id": prim["texture_id"],
            "is_transparent": prim["is_transparent"],
        }
        if base_color_override is not None:
            entry["base_color_factor"] = base_color_override
        elif "base_color_factor" in prim and prim["base_color_factor"] is not None:
            entry["base_color_factor"] = prim["base_color_factor"]
        instances.append(entry)
    return instances


# ---------------------------------------------------------------------------
# Scene parameters — easy to edit
# ---------------------------------------------------------------------------

# Floor
FLOOR_RADIUS = 30           # radio del piso circular (unidades de mundo)
FLOOR_TILE_REPEAT = 6           # how many times the floor texture tiles
FLOOR_BASE_SCALE = 0.1         # base scale before multiplying by FLOOR_TILE_REPEAT

# Forest — centro del anillo (donde esta Aang)
FOREST_CENTER_X = 0.0
FOREST_CENTER_Z = 0.0

# --- Troncos (trunks) ---
TRUNK_ENABLED = True
TRUNK_COUNT = 8
TRUNK_INNER_RADIUS = 5.0
TRUNK_OUTER_RADIUS = 20.0
TRUNK_SCALE_MIN = 0.02
TRUNK_SCALE_MAX = 0.06
TRUNK_SEED = 7
TRUNK_MESH_INDICES = [0, 37]

# --- Arboles tipo A (tree_a) ---
TREEA_ENABLED = True
TREEA_COUNT = 20
TREEA_INNER_RADIUS = 5.0
TREEA_OUTER_RADIUS = 20.0
TREEA_SCALE_MIN = 0.02
TREEA_SCALE_MAX = 0.06
TREEA_SEED = 13
TREEA_MESH_INDICES = [4, 6, 7, 8, 9, 10, 32]

# --- Arboles tipo B (tree_b) ---
TREEB_ENABLED = True
TREEB_COUNT = 40
TREEB_INNER_RADIUS = 5.0
TREEB_OUTER_RADIUS = 20.0
TREEB_SCALE_MIN = 0.05
TREEB_SCALE_MAX = 0.06
TREEB_SEED = 42
TREEB_MESH_INDICES = [3, 11, 12, 13, 14, 33]

# --- Rocas con musgo (mossy_rock) ---
MOSSY_ENABLED = True
MOSSY_COUNT = 30
MOSSY_INNER_RADIUS = 2.0
MOSSY_OUTER_RADIUS = 20.0
MOSSY_SCALE_MIN = 0.005
MOSSY_SCALE_MAX = 0.007
MOSSY_SEED = 99
MOSSY_MESH_INDICES = [0]
MOSSY_ASSET = "mossy_rock"

# Bushes (arbustos del asset arbusto/scene.gltf, 1 sola mesh)
BUSH_ENABLED = True
BUSH_COUNT = 30                  # cuantos arbustos colocar
BUSH_INNER_RADIUS = 10.0          # radio minimo al centro (mas cerca de Aang que los arboles)
BUSH_OUTER_RADIUS = 15.0         # radio maximo al centro (solapa con el inicio del rango de los arboles)
BUSH_SCALE_MIN = 0.005           # escala minima (arbustos son mas pequenos que los arboles)
BUSH_SCALE_MAX = 0.012           # escala maxima
BUSH_RING_BIAS = 0.0             # 0=anillo uniforme, 1=tendencia al borde externo
BUSH_Y_JITTER = 0.0              # pequeno jitter vertical (0 = todos apoyados en el suelo)
BUSH_SEED = 23                   # semilla del RNG (reproducible)

# Rock under Aang
ROCK_ENABLED = True
ROCK_SCALE = 0.1
ROCK_OFFSET_X = 0.0
ROCK_OFFSET_Z = 0.0
ROCK_OFFSET_Y = 0.4
ROCK_ROTATION_X_DEG = 90
ROCK_ROTATION_Y_DEG = 0
ROCK_ROTATION_Z_DEG = 0

# Particles (falling leaves)
PARTICLE_ENABLED = True
PARTICLE_MAX = 150
PARTICLE_SPAWN_RADIUS = 6.0
PARTICLE_CANOPY_HEIGHT = 5.0
PARTICLE_POINT_SIZE_SCALE = 20.0
PARTICLE_INITIAL_BURST = 80

# Camera
CAMERA_FOV_DEG = 45.0
CAMERA_OFFSET_X_MULT = 0.7       # initial eye offset multiplier
CAMERA_OFFSET_Y_MULT = 0.3
CAMERA_OFFSET_Z_MULT = 0.8

# Aang position & rotation
AANG_POS_X = 0.0
AANG_POS_Y = 0.0
AANG_POS_Z = 0.8
AANG_FACING_DEG = 0              # rotation around vertical axis




# ---------------------------------------------------------------------------
# Scene composition
# ---------------------------------------------------------------------------

def build_scene(phong_pipeline):
    """Load all static GLTF assets, create vertex lists, compose the scene.

    Returns a dict::

        {
            "primitives": [ {vertex_list, transform, texture_id, is_transparent}, ... ],
            "scene_scale": float,
            "scene_center": np.array([x, y, z]),
        }

    Aang is NOT loaded here (that is Task 8's responsibility).
    """
    white_tex = _make_white_texture()
    all_primitives = []

    # ------------------------------------------------------------------
    # 1. Rock under Aang
    # ------------------------------------------------------------------
    if ROCK_ENABLED:
        rock_prims = _load_asset(phong_pipeline, "rock_b", white_tex)
        if rock_prims:
            rock_transform = _placement(
                tx=ROCK_OFFSET_X, ty=ROCK_OFFSET_Y, tz=ROCK_OFFSET_Z,
                sx=ROCK_SCALE, sy=ROCK_SCALE, sz=ROCK_SCALE,
                rx=math.radians(ROCK_ROTATION_X_DEG),
                ry=math.radians(ROCK_ROTATION_Y_DEG),
                rz=math.radians(ROCK_ROTATION_Z_DEG),
            )
            all_primitives.extend(_instantiate(rock_prims, rock_transform))

    # ------------------------------------------------------------------
    # 2. Grass patches (distribuidos por todo el piso, acostados en el suelo)
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # 3. Forest — troncos, tree_a, tree_b por separado
    # ------------------------------------------------------------------
    if TRUNK_ENABLED:
        _scatter_forest_group(phong_pipeline, white_tex, TRUNK_MESH_INDICES,
                              TRUNK_COUNT, TRUNK_INNER_RADIUS, TRUNK_OUTER_RADIUS,
                              TRUNK_SCALE_MIN, TRUNK_SCALE_MAX, TRUNK_SEED,
                              FOREST_CENTER_X, FOREST_CENTER_Z, all_primitives)
    if TREEA_ENABLED:
        _scatter_forest_group(phong_pipeline, white_tex, TREEA_MESH_INDICES,
                              TREEA_COUNT, TREEA_INNER_RADIUS, TREEA_OUTER_RADIUS,
                              TREEA_SCALE_MIN, TREEA_SCALE_MAX, TREEA_SEED,
                              FOREST_CENTER_X, FOREST_CENTER_Z, all_primitives)
    if TREEB_ENABLED:
        _scatter_forest_group(phong_pipeline, white_tex, TREEB_MESH_INDICES,
                              TREEB_COUNT, TREEB_INNER_RADIUS, TREEB_OUTER_RADIUS,
                              TREEB_SCALE_MIN, TREEB_SCALE_MAX, TREEB_SEED,
                              FOREST_CENTER_X, FOREST_CENTER_Z, all_primitives)
    if MOSSY_ENABLED:
        _scatter_forest_group(phong_pipeline, white_tex, MOSSY_MESH_INDICES,
                              MOSSY_COUNT, MOSSY_INNER_RADIUS, MOSSY_OUTER_RADIUS,
                              MOSSY_SCALE_MIN, MOSSY_SCALE_MAX, MOSSY_SEED,
                              FOREST_CENTER_X, FOREST_CENTER_Z, all_primitives,
                              asset_name=MOSSY_ASSET)

    # ------------------------------------------------------------------
    # 4b. Bushes (arbustos del asset arbusto, repartidos alrededor de Aang)
    # ------------------------------------------------------------------
    if BUSH_ENABLED:
        bush_template = _load_bush_templates(phong_pipeline, white_tex)
        if bush_template is not None:
            bush_rng = np.random.default_rng(BUSH_SEED)
            prims, baked_min_y = bush_template
            cx_world = AANG_POS_X
            cz_world = AANG_POS_Z
            for _ in range(BUSH_COUNT):
                angle = bush_rng.uniform(0.0, 2.0 * math.pi)
                u = bush_rng.uniform(0.0, 1.0)
                r = (
                    BUSH_INNER_RADIUS
                    + (BUSH_OUTER_RADIUS - BUSH_INNER_RADIUS)
                    * (u * (1.0 - BUSH_RING_BIAS) + u ** 2 * BUSH_RING_BIAS)
                )
                tx = cx_world + r * math.cos(angle)
                tz = cz_world + r * math.sin(angle)
                s = bush_rng.uniform(BUSH_SCALE_MIN, BUSH_SCALE_MAX)
                ry = bush_rng.uniform(0.0, 2.0 * math.pi)
                ty = bush_rng.uniform(-BUSH_Y_JITTER, BUSH_Y_JITTER)
                ground_offset = -s * baked_min_y
                b_transform = _placement(
                    tx=tx, ty=ty + ground_offset, tz=tz,
                    sx=s, sy=s, sz=s, ry=ry,
                )
                all_primitives.extend(_instantiate(prims, b_transform))

    # ------------------------------------------------------------------
    # 5. Floor — piso circular con textura repetida
    # ------------------------------------------------------------------
    floor_prims = _make_circle_floor(phong_pipeline, FLOOR_RADIUS, segments=64)

    floor_img_path = ASSETS_DIR / "forested_floor" / "textures" / "floor_texture_baseColor.png"
    if floor_img_path.exists():
        img = Image.open(str(floor_img_path))
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        repeat_tex_id = texture_2D_setup(img, sWrapMode=GL_REPEAT, tWrapMode=GL_REPEAT, flip_top_bottom=False)
        for prim in floor_prims:
            prim["texture_id"] = repeat_tex_id
            n_floats = len(prim["vertex_list"].uv)
            uvs = np.array(prim["vertex_list"].uv[:], dtype=np.float32).reshape(n_floats // 2, 2)
            uvs *= float(FLOOR_TILE_REPEAT)
            prim["vertex_list"].uv[:] = uvs.flatten()

    floor_transform = tr.identity()
    all_primitives.extend(_instantiate(floor_prims, floor_transform))

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------
    scene_scale = 1.0
    scene_center = np.array([AANG_POS_X, AANG_POS_Y, AANG_POS_Z], dtype=np.float32)

    print(f"[scene_builder] total primitive instances: {len(all_primitives)}")

    return {
        "primitives": all_primitives,
        "scene_scale": scene_scale,
        "scene_center": scene_center,
    }
