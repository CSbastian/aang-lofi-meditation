# Draft: Adaptar escena Zuko vs. Ozai a assets GLTF (Azula reemplaza a Ozai)

## Original Request
"Te dejé los assets de zuko y azula (reemplazado por ozai) en formato .gltf, adapta la escena para este tipo de formato, revisa si tiene esqueleto para lograr el movimiento que requiere la escena y finalmente revisa que el codigo no de errores."

## Requirements (confirmed)
- Adaptar la escena `21004082-K/` para cargar modelos GLTF en vez de primitivas OFF
- Zuko → `assets/zuko_fortnite/scene.gltf`
- Azula (reemplaza a Ozai) → `assets/nasb2_-_azula/scene.gltf`
- Comprobar si tienen esqueleto
- Lograr el movimiento que requiere la escena (28s, 7 shots según `Escena.md`)
- Verificar que el código no dé errores

## Research Findings

### Assets GLTF
**Zuko (zuko_fortnite/scene.gltf)**:
- 332 nodos, 4 meshes, 2 skins (5 + 314 joints)
- Mallas SKINNED: tienen `JOINTS_0` + `WEIGHTS_0` (23,698 vértices totales)
- BBox Y: [0, 1.74] → altura 1.74m (Y-up, correcto)
- 0 animaciones incluidas
- 4 materiales pero `has_tex=False` en sus `baseColorTexture` → texturas no referenciadas desde el gltf, hay que mapear por nombre de material (igual que zorzal):
  - `M_MED_TikiTorch_Backpack` → `MI_TikiTorch_Backpack_diffuse.png` (ojo nombre inconsistente)
  - `MI_TikiTorch_Body` → `MI_TikiTorch_Body_diffuse.png`
  - `MI_TikiTorch_Head` → `MI_TikiTorch_Head_diffuse.png`
  - `MI_TikiTorch_FaceAcc` → `MI_TikiTorch_FaceAcc_diffuse.png`
- Root: `Sketchfab_model` (identity), 1 child → jerarquía anidada

**Azula (nasb2_-_azula/scene.gltf)**:
- 5 nodos, 3 meshes, 0 skins → **SIN ESQUELETO**
- Mallas RÍGIDAS (sin JOINTS_0)
- BBox Z: [0, 1.96] → **Z-up** (necesita rotación X -90°)
- 0 animaciones
- 2 materiales con `has_tex=True` → texturas referenciadas correctamente:
  - `Azula_Costume_01_Mat` → `Azula_Costume_01_Mat_baseColor.png`
  - `Azula_Expressions_Mat` → `Azula_Expressions_Mat_baseColor.png`

### Código actual (`21004082-K/`)
- `__init__.py`: entry point, scheduling, pausa/reset
- `environment.py`: construye sala con cube.off/cylinder.off (NO cambia)
- `zuko.py`: build_zuko con primitivas OFF + `apply_zuko_pose(joint_name -> 4x4)` sobre 12 joints custom (torso, brazo_der, etc.)
- `ozai.py`: build_ozai con primitivas OFF + `apply_ozai_pose` sobre 2 joints (ozai_torso, ozai_cabeza)
- `director.py`: timeline 28s, 7 shots, llama `apply_zuko_pose` / `apply_ozai_pose` con `ZUKO_POSES` / `OZAI_POSES` basados en nombres custom
- `camera.py`: 7 tomas calibradas para Zuko en z=+2 (Y ~1-2m) y Ozai en z=-3
- `lighting.py`: 1 PointLight + 2 SpotLights + Material, Fire Nation warm tones

### Shader actual (`vertex_program.glsl` / `fragment_program.glsl`)
- Atributos: `in vec3 position`, `in vec3 color`, `in vec3 normal`
- NO soporta texturas (usa `in vec3 color` por vértice)
- NO soporta skinning (no `JOINTS_0`/`WEIGHTS_0` ni `skin_matrices[]`)
- Illuminación: PointLight + 2 SpotLights + Material

### Loader GLTF (`grafica/gltf.py`)
- Soporta skinning (skins + inverse bind matrices), animaciones LINEAR, materials baseColorTexture, nodes TRS
- Método `sample_animation` y `node_trs_with_overrides`
- Carga texturas con `upload_textures()`

### Patrón skinning (`examples/skinning/__init__.py`)
- Construye Scenegraph con un nodo `gltf_node_N` por cada nodo GLTF (jerarquía)
- NO usa mesh_instances del Scenegraph → construye `vertex_list` propio en el pipeline
- Shaders LBS (`skin_matrices[N]` mat4 array) y DQS (`dual_quat_real[N]` + `dual_quat_dual[N]` vec4 arrays)
- **HARDCODED `SHADER_JOINTS = 91`** en el ejemplo zorzal → para Zuko con 314 joints hay que ajustar los shaders.
- `compute_skin_matrices` recorre joints, aplica `joint_global @ inverse_bind_matrix`
- LBS = N*16 floats; DQS = N*8 floats (más compacto)
- Con 314 joints: LBS = 314*16 = 5024 floats; DQS = 314*8 = 2512 floats. OpenGL `GL_MAX_VERTEX_UNIFORM_VECTORS` mínimo 256, típico 4096 — **314 joints con LBS puede fallar** en GPUs móviles/integradas; DQS puede ser más seguro.

### Patrón animación_rígida (`examples/animacion_esqueletica/__init__.py`)
- Skipped primitivas con joints (no skinning)
- Usa mesh_instances del Scenegraph con texturas
- `_build_mesh_node` construye dict de malla con `texture=texture_id`, `uv`, sin `joints`
- Animación: aplica TRS overrides del GLTF a los nodos del grafo
- Auto-detección Z-up/X-up vía bbox → aplica `root_fixup`

## Technical Decisions
- Reemplazar OFF por GLTF usando `grafica.gltf.GltfModel` ✓
- Texturas: mapear manualmente material→filename para Zuko (texturas no referenciadas) ✓
- Azula: rotación X -90° (Z-up → Y-up) + traducir a z=-3 (trono) ✓
- Zuko: Y-up correcto, escalar/rotar para framebuffer Y=[0,1.74] similar al anterior ✓

## Decisions (resueltas por el usuario)

1. **Skinning**: DQS (Dual Quaternion Skinning) para Zuko (314 joints). GPU confirmado: `GL_MAX_VERTEX_UNIFORM_VECTORS = 4096` → 628 vec4 con DQS, dentro del límite. ✓
2. **Azula**: estática todo el tiempo (sin animación) — justificado por "imperturbable/estoico" en Escena.md
3. **Poses de Zuko**: 7 poses completas adaptadas a los joints del GLTF de Zuko.

## Mapeo de joints Zuko (skin[1] de 314 joints)

Nombre Unreal/Fortnite — nombre del código actual:

| Código actual (12 joints) | GLTF skin[1] joint |
|---------------------------|--------------------|
| torso | `spine_05_013` (joint[7]) — columna alta |
| cabeza | `head_018` (joint[13]) |
| brazo_der | `upperarm_r_0118` (joint[184]) |
| antebrazo_der | `lowerarm_r_0119` (joint[185]) |
| mano_der | `hand_r_0120` (joint[186]) |
| brazo_izq | `upperarm_l_078` (joint[128]) |
| antebrazo_izq | `lowerarm_l_079` (joint[129]) |
| mano_izq | `hand_l_080` (joint[130]) |
| muslo_der | `thigh_r_0167` (joint[254]) |
| pantorrilla_der | `calf_r_0168` (joint[255]) |
| muslo_izq | `thigh_l_0159` (joint[241]) |
| pantorrilla_izq | `calf_l_0160` (joint[242]) |

## Pipeline / shader strategy

- **`lit_textured_skinned`**: shader para Zuko (con DQS skinning + texturas + ilum P/Spot/Material)
- **`lit_textured`**: shader para Azula y entorno (sin skinning, con texturas + ilum P/Spot/Material). El entorno (floor, walls, throne) puede seguir usando `lit` con color por vértice (assets/cube.off, cylinder.off) — sin cambios a environment.py.
- Materiales Zuko: texturas `textures/*.png` NO referenciadas en gltf → mapear por nombre de material:
  - `M_MED_TikiTorch_Backpack` → `M_MED_TikiTorch_Backpack_diffuse.png`
  - `MI_TikiTorch_Body` → `MI_TikiTorch_Body_diffuse.png`
  - `MI_TikiTorch_Head` → `MI_TikiTorch_Head_diffuse.png`
  - `MI_TikiTorch_FaceAcc` → `MI_TikiTorch_FaceAcc_diffuse.png`
- Azula: texturas referenciadas correctamente ✓
- Root fixup Zuko: NO necesario (Y-up). Sí aplicar `tr.translate(0, 0, 2)` para posicionarlo al frente.
- Root fixup Azula: aplicar `tr.rotationX(-π/2)` (Z-up → Y-up) y `tr.translate(0, 0, -3)` para el trono.

## Metis Review Findings (resueltas como defaults)

1. **Shader architecture** (Metis flagged): Escribir un NUEVO shader DQS+Phong que combina DQS skinning del ejemplo skinning + Phong lighting (PointLight + SpotLight + Material structs) del shader actual. ~200 líneas nuevas de GLSL.
2. **Backpack (Zuko skin[0], 5 joints)**: SKIP mesh 0 (`M_MED_TikiTorch_Pack_LOD0`) para evitar importar skin matriz 5-joints — simplifica el pipeline. Default aplicado.
3. **Pose adaptation**: Las 7 poses se RE-AUTORAN desde cero para el skeleton GLTF. Las rotaciones previas (OFF-primitive rig) no se mapean — se redefinen con feedback visual iterativo.
4. **Wrapper nodes incluidos**: Los 3 wrappers (`Sketchfab_model`, FBX model, `RootNode`) tienen `matrix_override` (NO TRS simple). El FBX model aplica scale 0.01 necesario. INCLUIR los 332 nodes en el Scenegraph, NO saltar wrappers.
5. **Multi-pipeline render loop**: `__init__.py` hace `graph.render()` (entorno + Azula) + bucle custom de Zuko (compute skin matrices + upload DQS uniforms + draw primitives con vertex_list propio). NO usar `graph.render()` para Zuko skinned.
6. **`update_lighting_pipeline` debe empujar uniforms a TODOS los pipelines** (`"lit"`, `"zuko_dqs"`, `"azula_lit"`), no solo `"lit"`.
7. **`KHR_materials_pbrSpecularGlossiness`**: el loader `grafica/gltf.py` no lee extensiones → `base_color_texture=None` confirmado. Mapeo manual por nombre de material (como el zorzal).
8. **Side-by-side principle**: NO modificar `grafica/gltf.py`, solo adaptar dentro de `21004082-K/`.
9. **Twist joints**: `lowerarm_twist_01_l`, etc. NO se animan (quedan en bind pose).
10. **IK/eye_control joints**: `hand_ik_*`, `pole_elbow_*`, `eye_control_*` NO se animan (handlers, no afectan malla).
11. **Skin[[1]] vs skin[0]**: Solo usar skin[1] (314 joints, el cuerpo principal). Meshes con skin[0] (backpack) se SALTAN.

## Pose Joint Name → GLTF Joint Mapping (Skin[1])

| Logical pose joint (in ZUKO_POSES dict keys) | GLTF joint NAME | joint index in skin[1] (col=slice index) |
|----------------------------------------------|-----------------|-----------------------------------------|
| `torso` | `spine_05_013` | 7 |
| `cabeza` | `head_018` | 13 |
| `brazo_der` | `upperarm_r_0118` | 184 |
| `antebrazo_der` | `lowerarm_r_0119` | 185 |
| `mano_der` | `hand_r_0120` | 186 |
| `brazo_izq` | `upperarm_l_078` | 128 |
| `antebrazo_izq` | `lowerarm_l_079` | 129 |
| `mano_izq` | `hand_l_080` | 130 |
| `muslo_der` | `thigh_r_0167` | 254 |
| `pantorrilla_der` | `calf_r_0168` | 255 |
| `muslo_izq` | `thigh_l_0159` | 241 |
| `pantorrilla_izq` | `calf_l_0160` | 242 |

## Test Strategy
- No hay test automatizados en el repo (per AGENTS.md).
- QA es VISUAL y MANUAL: arrancar la escena y verificar visualmente.
- **Agent-Executed QA**:
  - Lanzar la escena `uv run python -m 21004082-K` en tmux con timeout de 30s sin crash; verificar código de salida.
  - Lanzar el comando `uv run python caja_de_juguetes.py tarea` y validar salida.
  - Screenshot via Playwright/pyglet si es alcanzable (no se interactúa sino se abre la ventana).
  - Verificar que `uv run python -m py_compile 21004082-K/*.py` no arroja SyntaxError.
  - Verificar imports (no NameError al cargar(parsear).

## Scope Boundaries
- INCLUDE:
  - Carga GLTF (Zuko con DQS skinning + Azula estática)
  - Barras/escala root_fixup para Azula
  - Texturas (mapeo manual de Zuko, directa de Azula)
  - Nuevos shaders combinando iluminación actual + texturas + DQS skinning
  - Reescribir `zuko.py` para usar GLTFModel y apply pose sobre joints del skin
  - Reescribir `ozai.py` → `azula.py` (?o renombrar nodo en código) como mesh estática
  - Mantener environment.py / camera.py / lighting.py (sin cambios esperados)
  - Adaptar director.py para invocar apply_zuko_pose con el modelo GLTF cargado
  - Actualizar `__init__.py` para construir la escena con GLTF
  - Verificar que arranca sin errores
- EXCLUDE:
  - Cambiar environment.py (sala del trono sigue con OFFs)
  - Cambiar camera.py (7 shots calibrados — mantener)
  - Cambiar lighting.py (Fire Nation warm tones — mantener)
  - Crear nuevas animaciones GLTF externas — todo es programático en Python.

## Scope Boundaries
- INCLUDE: Carga de GLTF, integración con Scenegraph, skinning o rígido (según decisión), texturas, iluminación preservada, animación manual de poses, shaders nuevos, verificación sin errores
- EXCLUDE: Cambiar environment.py (la sala del trono sigue con OFFs), cambiar camera.py (mantener 7 shots), cambiar lighting.py (Fire Nation)