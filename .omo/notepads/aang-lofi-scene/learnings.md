
## Shader Creation

- Created `21004082-K/shaders/skinning_lbs_vertex.glsl` — LBS vertex shader adapted from `examples/skinning/vertex_program_lbs.glsl` with `skin_matrices[330]` (Aang has 330 joints, changed from 91 in the reference).
- Created `21004082-K/shaders/skinning_phong_fragment.glsl` — Phong+fog fragment shader with `alpha_cutoff`, matching the pattern from `21004082-K/shaders/phong_fragment.glsl`.
- Both files use `#version 330`.
- Vertex inputs: `position`, `normal`, `uv`, `joints`, `weights` — standard 4-influence LBS.
- Fragment shader discards fragments with `sampled.a < alpha_cutoff` before lighting.

## Cámara (camera.py)

- `Arcball.pose` es cámara-a-mundo (4x4). La matriz de vista para los
  shaders es `np.linalg.inv(pose)`. Es el patrón de todo el repo (skinning,
  arcball_example, etc.).
- `forward = -pose[:3, 2]` y `right = pose[:3, 0]` salen de las columnas
  de la pose. El `-Z` viene de que las cámaras OpenGL miran a lo largo
  de `-Z` en espacio de vista.
- Para WASD "horizontal" hay que aplanar forward/right a `y=0` y
  renormalizar. Si no, mover la cámara hacia arriba se siente raro
  (camina en diagonal sobre el aire). Lo que se mueve no es la cámara
  sino `arcball.target`: el Arcball ya se encarga de mantener la pose
  orientada hacia él.
- Damping frame-rate-independent: `alpha = 1 - exp(-damping_alpha * dt * 60)`.
  A 60 fps el factor efectivo es exactamente `damping_alpha`; si el
  frame rate cae, integramos más tiempo en un solo paso y la sensación
  no cambia.
- Damping de pose con lerp de matrices (no slerp) basta para amplitudes
  pequeñas (alpha < ~0.2). El ojo no distingue. Eso evita convertir a
  cuaternión en cada frame.
- Llamar `arcball.stabilize_rotation()` después del lerp evita que se
  acumule drift de punto flotante en las columnas de rotación.
- Para no importar `pyglet.window` ni `pyglet.key` dentro de `camera.py`,
  hardcodeamos los códigos de botón (`1, 2, 4`) y de tecla (`97-100`).
  El módulo queda testeable sin abrir una ventana.
- `set_distance_limits(min=0.2*scale, max=6*scale)` es la convención del
  repo (`examples/skinning/__init__.py:464`). Lo replicamos en el
  `__init__` de LoFiCamera.

## Renderer de partículas (`setup_particle_renderer` / `render_particles`)

- `pipeline.vertex_list(n, GL.GL_POINTS, position="f", color="f", size="f")`
  — usa `vertex_list` (no `_indexed`): un punto = un vértice, sin índices.
  El `GL_POINTS` constante va como segundo arg posicional.
- Atributos mapean 1:1 a `particle_vertex.glsl`: `position`→vec3,
  `color`→vec4, `size`→float. Los códigos `"f"` de pyglet son float32.
- `vl.position[:] = positions[:n].flatten()` — hay que **flatten** porque
  el atributo en el vertex_list es plano (`n*3` floats), no `(n,3)`.
  Mismo truco para `color` (`n*4`) y `size` (`n`).
- `pipeline["view"] = view.reshape(16, 1, order="F")` — orden column-major
  (Fortran) para OpenGL. Mismo patrón que en `scene_builder.py` para
  las matrices de los modelos.
- `pipeline.use()` antes de tocar uniforms — sin esto los uniforms van
  al programa anterior.
- `vl.draw(GL.GL_POINTS, count=n)` — `count` limita a los activos sin
  tocar el resto del buffer (pre-reservado a `max_particles`).
- `import pyglet.gl as GL` dentro de las funciones: mismo patrón que
  `aang.py` y mantiene el módulo importable sin GL context (útil para
  tests que sólo instancien `ParticleSystem3D`).
- `get_gpu_data()` ya devuelve copias contiguas → safe subir directo
  sin clonar otra vez. `draw_count()` ya devuelve `int` (no `np.bool_`)
  → se puede usar directo como `count`.
- `min(n, max_n)` por seguridad: si en algún frame hay más activas que
  el pool del renderer, no overfloweamos el buffer GPU.
- Snapshot de pose/target al `down()` y snapshot en cada `scroll()`:
  sino el damping ve un delta brusco y la cámara "tira" hacia la pose
  intermedia.

## Partículas 3D (`21004082-K/particles3d.py`)

### Patrón SoA adaptado a 3D
- Misma idea que `grafica/particle.py` (struct of arrays) pero en `dims=3`:
  `positions` y `velocities` son `(N, 3)`; `colors` `(N, 4)`; `sizes`/`ages`/`ttls`/`active` `(N,)`.
- Diferencia clave: aquí NO se compacta el array. Se usa una máscara
  `active` y `np.where(~self.active)[0][:n]` para encontrar huecos al emitir.
  Esto evita O(N) shuffles por frame — más simple, suficiente para N=150.
- `grafica/particle.py` en cambio mantiene un índice `n` y compacta
  (`_compact`) tras cada update: más rápido en CPU pero requiere ordenar
  el orden de muerte. Para 150 partículas el costo es despreciable.

### Convenciones del proyecto respetadas
- `np.float32` en todos los buffers para compatibilidad con OpenGL.
- `get_gpu_data()` devuelve arrays contiguos listos para
  `pyglet.graphics.vertex_list` con `GL_POINTS` (tarea 3). Devuelve
  `.copy()` para que mutar el resultado no afecte al sistema.
- `draw_count()` devuelve `int` (no `np.bool_` ni similares) — seguro
  para usar en condicionales Python.

### Movimiento "lo-fi"
- Velocidad base hacia arriba 0.08–0.25 unidades/s, drift horizontal ±0.05.
- Turbulencia sinusoidal por índice de partícula (`sin(t*2 + i*0.1)`) →
  cada espora tiene fase propia, nada se mueve igual. Magnitud pequeña
  (`* dt * 0.01`) para que se sienta perezoso, no errático.
- TTL 8–15s + altura `spawn_center.y + 5.5` → muerte natural antes de
  llegar al techo visual. Auto-respawn al bajar del 70% mantiene
  densidad estable sin necesidad de llamar `emit()` cada frame.

### Color firefly/spore
- Canal R 0.7–1.0, G 0.9–1.0, B 0.3–0.5, A 0.6–0.8 → amarillo-verde
  pálido. Cumple Escena.md: "puntos de luz amarilla/verde pálida,
  flotando de abajo hacia arriba en patrones caóticos y suaves".

### Verificación (con `np.random.seed(42)`)
- `emit(50)` → `draw_count() == 50`.
- 100× `update(0.1)` (10s) → `draw_count() == 111` (auto-respawn disparó).
- 500× `update(0.1)` (50s, muy por encima del TTL) → `draw_count() == 116`,
  siempre ≤ 150.
- Rango Y activo [0.27, 3.38] confirma movimiento ascendente real.

### Gotcha: nombre del módulo con guion
- El directorio `21004082-K` contiene un guion, así que
  `import 21004082-K.particles3d` no funciona. Usar
  `importlib.util.spec_from_file_location(...)` desde tests/scripts
  externos. La tarea 3 (shader/draw) debe decidir cómo se importa
  (probablemente `sys.path.insert(0, "21004082-K")` desde el runner).

## Audio Module

- Created `21004082-K/audio.py` — Lo-Fi audio loading via `pyglet.media` with graceful degradation.
  - `load_lofi_audio(audio_path)` → returns `pyglet.media.Player` with looping, or `None` on failure.
  - `toggle_audio(player)` → pauses if playing, resumes if paused. Safe with `None`.
  - `set_audio_volume(player, volume)` → clamps 0.0–1.0. Safe with `None`.
  - Missing/corrupt files print a warning and return `None` — no crash.
  - Created `21004082-K/assets/audio/` directory for storing audio files.
  - Uses `player.loop = True` for native looping (confirmed via Context7 docs for pyglet 2.1.13).
   - Package name has hyphen (`21004082-K`) — direct `import` not possible, use `importlib` or `-m` flag.

## Scene Builder (`21004082-K/scene_builder.py`)

### GLTF loading pattern
- `GltfModel(path)` parses the file; `model.meshes` is `list[list[GltfPrimitive]]`.
- Each `GltfPrimitive` has `.positions`, `.normals`, `.uvs`, `.indices`, `.material_index`.
- `model.upload_textures()` must be called with an active OpenGL context — it populates `model.texture_gl_ids`.
- `model.materials[i]` is a dict with `base_color_factor` (vec4), `base_color_texture` (int|None), `name`.
- After extracting vertex data and texture IDs, `del model` frees CPU-side buffers.

### Vertex list creation
- `pipeline.vertex_list_indexed(n_verts, GL.GL_TRIANGLES, indices.tolist())` — indices must be a Python list.
- Attributes set via `vl.position[:] = positions.flatten()`, same for `.normal` and `.uv`.
- If normals/uvs are `None` in the GLTF, fill with defaults (up vector / zeros).

### Scene composition
- Giant tree (tree grande) at (3,0,1) with scale 3.5x and -15° Y rotation frames the right side.
- Mushrooms instanced 5× on the tree trunk at varying heights (y=0.5–3.0), rotated toward center.
- Cliff shrub repurposed as purple rock wall: scale (5,2,0.5) at z=-2, base_color_factor override to (0.6,0.3,0.7).
- Background trees in 4 layers (z=-5,-8,-12,-16) with capped 20 instances total.
- Grass scattered in 8 instances around origin on y=0 plane.
- `_placement()` helper: translate @ rotateY @ scale — sufficient for static scene objects.
- `_instantiate()` shares vertex_lists across instances (same GPU buffer, different transforms).

## Joint Animation (`21004082-K/aang.py` → `apply_breathing_and_wind`)

### Pattern: fresh base each frame
- Animation override = `graph.nodes[name]["transform"] = base_transforms[name] @ tr.rotationX(theta)`.
- Always re-read from `base_transforms` (pre-stored in `setup_aang` as
  `node.local_matrix().copy()`). Never compound on the previous frame's
  transform — that would explode the rotation.
- `base_transforms` is keyed by scenegraph node name
  (`gltf_node_<idx>`), same names used in `node_to_scenegraph_name`.

### Static-vs-dynamic split
- Head tilt is a one-shot: applied on `first_call=True` only. Subsequent
  frames leave the head transform alone (no entry in the breathing/cape
  loops), so the tilt persists. The `if first_call:` guard does NOT need
  to write back into `base_transforms` — the matrix lives on the graph
  node until something else overwrites it.
- Breathing (spine 8–12) and wind (cape 14–17) recompute every frame
  from `sin(2*pi*f*t + phase)`.

### Joint index mapping (Aang GLTF)
- Spine: 8, 9, 10, 11, 12 — single X rotation, amplitude 0.02 rad,
  0.5 Hz (2 s cycle). Subtle by design (Lo-Fi mood).
- Cape: 14, 15, 16, 17 — Z rotation, amplitude 0.08 rad, 0.3 Hz,
  phase offset = `i * 0.8` rad between consecutive joints → wave.
- Head: 20 — `rotationX(-0.1)` (~6 deg down) on first call.

### Defensive guards
- `if idx >= len(n2s)` and `if node_name not in base_transforms` keep
  the function robust if the GLTF ever drops/renames a joint. Silent
  skip is fine for Lo-Fi — better than crashing the render loop.

### Verification
- At `t=0` breath term is 0, so `spine0.transform == base` exactly.
- Re-running at a different `t` produces a *fresh* base @ rotation,
  not a compounded one. Asserted via `np.allclose` against the
  recomputed expected matrix.
- Cape phase offset yields distinct transforms per joint at the same
  `t` (verified for all 4 pairs at t=0).
- Head transform is identical between two non-first calls
  (tilt persists, no re-apply, no drift).

### Gotcha: `tr.rotationX` requires `grafica.transformations` import
- Added `from grafica import transformations as tr` at the top of
  `aang.py` (was not present in Task 8). Keeps it consistent with the
  other examples that use `tr` as the local shorthand.
