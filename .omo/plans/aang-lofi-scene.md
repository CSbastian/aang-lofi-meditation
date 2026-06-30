# Escena 3D de Aang Meditando (Lo-Fi)

## TL;DR

> **Quick Summary**: Implementar una escena 3D interactiva de Aang meditando con ambiente Lo-Fi, usando skinning LBS para el personaje (con respiración y viento en capa animados via joints), iluminación Phong, partículas 3D flotantes, niebla por distancia, cámara orbital con WASD+damping, y audio Lo-Fi en loop. Todo sobre la librería `grafica/` del curso CC3501.
>
> **Deliverables**:
> - Comando click `tarea(width, height)` en `21004082-K/__init__.py` que renderiza la escena completa
> - Shaders GLSL: Phong (estático), LBS+Phong (Aang), partículas (puntos 3D)
> - Módulos Python: cámara custom, sistema de partículas 3D, audio, composición de escena
> - Escena: Aang central + árbol gigante derecho + hongos + muro roca púrpura + árboles multicapa + arbustos + pasto + partículas + niebla + audio
>
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Task 1 (Phong shaders) → Task 7 (scene composition) → Task 12 (main entry point) → F1-F4

---

## Context

### Original Request
Implementar en `21004082-K/` la escena descrita en `21004082-K/Escena.md`: Aang meditando con música Lo-Fi, cámara interactiva (teclado + ratón), fondo con árboles/arbustos/hongos, partículas mágicas, niebla, y post-procesamiento. Assets glTF provistos en `21004082-K/assets/`.

### Interview Summary
**Key Discussions**:
- **Audio**: El usuario proveerá el archivo de audio Lo-Fi. El plan asume que existirá en `21004082-K/assets/audio/` con nombre configurable.
- **Fidelidad**: Aproximaciones educacionales con énfasis en sistema de iluminación Phong + partículas flotantes. Sin cloth physics real, sin DoF, sin niebla volumétrica real.
- **Pose de Aang**: Usar skinning (esqueletos/LBS). El modelo viene de pie (T-pose de Fortnite, 330 joints, sin animaciones). Se mantiene pose de pie con respiración + viento en capa via animación manual de joints. Postura de loto excluida por complejidad (330 joints).
- **Testing**: QA visual sin tests automatizados (el repo no tiene framework de tests).

**Research Findings**:
- `grafica/` tiene 18 módulos: Scenegraph, transformations, Arcball camera, GltfModel (con skinning), textures, background, particle (2D), framebuffers, etc.
- NO tiene: shaders Phong, fog, audio, partículas 3D → construir desde cero
- `examples/skinning/__init__.py` (667 líneas) es la referencia exacta para LBS skinning con GLTF + Arcball + I/O completo
- `examples/skinning/vertex_program_lbs.glsl` tiene shader LBS (hardcoded 91 joints → cambiar a 330)
- `examples/skinning/fragment_program.glsl` tiene ambient+diffuse → extender con specular Phong + fog
- Aang: 330 skin joints, 2 meshes, 2 texturas, sin animaciones
- Assets estáticos: todos sin skinning, cargables con GltfModel + pipeline estándar
- `referencia.png` no pudo analizarse (timeout) — se procede con descripción de Escena.md

### Metis Review
**Identified Gaps** (addressed):
- Joint count en shader LBS debe ser 330 (no 91 del ejemplo): Se incluye como nota explícita en Task 2
- `upload_textures()` debe llamarse después de crear contexto OpenGL (después de Window): Se documenta en orden de inicialización
- Audio debe degradar graciosamente si el archivo no existe: Se incluye como criterio de aceptación
- Damping del ratón: Arcball no tiene damping nativo → se añade lerp en el wrapper de cámara
- Partículas 3D: grafica/particle.py es 2D solo → se construye sistema 3D custom

---

## Work Objectives

### Core Objective
Construir una escena 3D interactiva y atmosférica de Aang meditando en un bosque místico, con iluminación Phong, partículas flotantes, niebla, cámara orbital suave, y audio Lo-Fi en loop — todo renderizado con Pyglet/PyOpenGL sobre la librería `grafica/`.

### Concrete Deliverables
- `21004082-K/__init__.py` — comando click `tarea` que ejecuta la escena completa
- `21004082-K/shaders/phong_vertex.glsl` — vertex shader Phong para objetos estáticos
- `21004082-K/shaders/phong_fragment.glsl` — fragment shader Phong con niebla por distancia
- `21004082-K/shaders/skinning_lbs_vertex.glsl` — vertex shader LBS (330 joints) para Aang
- `21004082-K/shaders/skinning_phong_fragment.glsl` — fragment shader Phong+fog para Aang
- `21004082-K/shaders/particle_vertex.glsl` — vertex shader para partículas 3D (puntos)
- `21004082-K/shaders/particle_fragment.glsl` — fragment shader para partículas (puntos luminosos)
- `21004082-K/camera.py` — controller de cámara (Arcball wrapper + WASD + damping + límites)
- `21004082-K/particles3d.py` — sistema de partículas 3D (esporas/luciérnagas)
- `21004082-K/audio.py` — cargador de audio Lo-Fi con loop (pyglet.media)
- `21004082-K/scene_builder.py` — composición de escena (jerarquía Scenegraph + placement)
- `21004082-K/aang.py` — integración de Aang (skinning + respiración + viento en capa)

### Definition of Done
- [ ] `uv run python caja_de_juguetes.py tarea` abre una ventana con la escena 3D
- [ ] Aang se renderiza correctamente con skinning LBS (malla deformada por esqueleto)
- [ ] La respiración de Aang es visible (pecho/spine se infla/desinfla sutilmente)
- [ ] El viento mueve la capa de Aang (joints de cape animados)
- [ ] Árboles, hongos, muro de roca, arbustos y pasto se renderizan con iluminación Phong
- [ ] Partículas 3D (puntos amarillo/verde pálido) flotan alrededor de Aang hacia arriba
- [ ] Niebla verde-amarillenta por distancia es visible en el fondo
- [ ] Ratón orbita la cámara alrededor de Aang con suavizado (damping)
- [ ] WASD desplaza la cámara con límites (no rompe composición)
- [ ] Audio Lo-Fi reproduce en loop (o degrada graciosamente si no hay archivo)
- [ ] La ventana no crashea y el FPS es razonable (>30)

### Must Have
- Iluminación Phong (ambient + diffuse + specular) en todos los objetos
- Skinning LBS para Aang con 330 joints
- Animación de respiración (spine joints, sinusoidal, ciclo lento)
- Animación de viento en capa (cape joints, sinusoidal, ciclo lento)
- Sistema de partículas 3D (puntos, float upward, respawn, color amarillo/verde pálido)
- Niebla por distancia (mix lineal por profundidad en fragment shader, color verde-amarillento)
- Cámara orbital (Arcball) con ratón + damping (lerp pose)
- Cámara WASD con límites de posición (bounding box clamp)
- Audio Lo-Fi en loop (pyglet.media, degradación graciosa si no hay archivo)
- Composición: Aang centro, árbol gigante derecha, hongos en árbol, muro púrpura detrás, árboles multicapa fondo, arbustos, pasto
- Fondo gradiente (GradientBackground existente, colores atmosféricos)
- HUD con instrucciones de controles

### Must NOT Have (Guardrails)
- NO modificar archivos de `grafica/` — solo crear archivos nuevos en `21004082-K/`
- NO cloth physics real (Verlet/pymunk) — usar animación de joints
- NO depth of field / post-procesamiento de framebuffer — fuera de scope
- NO niebla volumétrica con raymarching — usar niebla por distancia en shader
- NO reponer Aang a postura de loto (330 joints, inviable) — mantener pose de pie
- NO tests automatizados (pytest/unittest) — el repo no tiene framework de tests
- NO soporte .glb (solo .gltf + .bin)
- NO shadow mapping — fuera de scope
- NO normal maps / occlusion / emissive — el GltfModel no los soporta
- NO modificar `caja_de_juguetes.py` — el comando `tarea` ya está registrado
- NO abstracción excesiva — código directo y legible, estilo educacional
- NO comentarios excesivos — estilo del repo (español o inglés, conciso)
- NO `as any` / `@ts-ignore` / empty catches / console.log en prod (patrones AI slop)

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** - ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO (repo no tiene pytest/unittest)
- **Automated tests**: None
- **Framework**: none
- **QA**: Visual + runtime verification via agent

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.omo/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Shaders**: Usar Bash (grep) — verificar sintaxis GLSL, buscar typos en uniforms
- **Módulos Python**: Usar Bash (uv run python -c) — importar módulo, verificar sin crashes
- **Escena completa**: Usar Bash (uv run python caja_de_juguetes.py tarea) — abrir ventana, verificar que renderiza, capturar screenshot via xvfb si es posible
- **Audio**: Usar Bash — verificar que pyglet.media carga sin crash
- **Partículas**: Usar Bash (uv run python -c) — instanciar sistema, verificar update() sin crash

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately - shaders + utilities, all independent):
├── Task 1: Phong shaders for static objects (vertex + fragment GLSL) [quick]
├── Task 2: Skinning LBS + Phong shaders for Aang (330 joints) [quick]
├── Task 3: Particle 3D shaders (vertex + fragment GLSL) [quick]
├── Task 4: Camera controller (Arcball + WASD + damping + limits) [unspecified-high]
├── Task 5: 3D particle system logic (Python, extend pattern from grafica/particle.py) [unspecified-high]
├── Task 6: Audio module (pyglet.media loader with loop + graceful degradation) [quick]

Wave 2 (After Wave 1 - scene assembly + integration, MAX PARALLEL):
├── Task 7: GLTF asset loader + scene composition (trees, mushrooms, rock wall, bushes, grass) [deep]
├── Task 8: Aang skinning integration (load model, build joint graph, compute skin matrices, custom vertex lists) [deep]
├── Task 9: Aang breathing + cape wind animation (manual joint overrides, sinusoidal) [unspecified-high]
├── Task 10: Particle integration (spawn around Aang, float up, respawn, color/size) [unspecified-high]
├── Task 11: Fog integration in Phong shaders (distance-based, green-yellow) [quick]
├── Task 12: Background + lighting setup (GradientBackground colors, light direction, ambient) [quick]

Wave 3 (After Wave 2 - final integration):
├── Task 13: Main entry point tarea() — window, wire everything, event handlers, draw loop, update loop [deep]
└── Task 14: HUD overlay (controls help, info text, FiraCode labels) [quick]

Wave FINAL (After ALL tasks — 4 parallel reviews, then user okay):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)
-> Present results -> Get explicit user okay

Critical Path: Task 1 → Task 7 → Task 13 → F1-F4
Parallel Speedup: ~65% faster than sequential
Max Concurrent: 6 (Wave 1)
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | — | 7, 11, 12 | 1 |
| 2 | — | 8, 11 | 1 |
| 3 | — | 10 | 1 |
| 4 | — | 13 | 1 |
| 5 | — | 10 | 1 |
| 6 | — | 13 | 1 |
| 7 | 1 | 13 | 2 |
| 8 | 2 | 9, 10, 13 | 2 |
| 9 | 8 | 13 | 2 |
| 10 | 3, 5, 8 | 13 | 2 |
| 11 | 1, 2 | 13 | 2 |
| 12 | 1 | 13 | 2 |
| 13 | 4, 5, 6, 7, 8, 9, 10, 11, 12 | 14, F1-F4 | 3 |
| 14 | 13 | F1-F4 | 3 |

### Agent Dispatch Summary

- **Wave 1**: **6** — T1 → `quick`, T2 → `quick`, T3 → `quick`, T4 → `unspecified-high`, T5 → `unspecified-high`, T6 → `quick`
- **Wave 2**: **6** — T7 → `deep`, T8 → `deep`, T9 → `unspecified-high`, T10 → `unspecified-high`, T11 → `quick`, T12 → `quick`
- **Wave 3**: **2** — T13 → `deep`, T14 → `quick`
- **FINAL**: **4** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [x] 1. Phong Shaders para Objetos Estáticos (vertex + fragment GLSL)

  **What to do**:
  - Crear `21004082-K/shaders/phong_vertex.glsl`: pasar position, normal, uv al fragment shader. Calcular world_position y world_normal. Aplicar transform (model matrix), view, projection. Outputs: world_position, world_normal, frag_uv al fragment shader.
  - Crear `21004082-K/shaders/phong_fragment.glsl`: implementar iluminación Phong completa:
    - Uniforms: `sampler2D diffuse_texture`, `vec3 light_direction`, `vec3 light_color`, `vec3 camera_position`, `float ambient_strength`, `float shininess`, `vec3 base_color_factor`, `vec4 fog_color`, `float fog_density` (o `fog_near`/`fog_far`)
    - Ambient: `ambient_strength * light_color * albedo`
    - Diffuse: `max(dot(normal, light), 0.0) * light_color * albedo`
    - Specular: `pow(max(dot(reflect(-light, normal), view_dir), 0.0), shininess) * light_color`
    - Niebla por distancia: calcular `depth = length(world_position - camera_position)`, `fog_factor = smoothstep(fog_near, fog_far, depth)` o `1.0 - exp(-fog_density * depth)`, mezclar `mix(phong_color, fog_color.rgb, fog_factor)`
    - Alpha: respetar `sampled.a`
  - Usar `#version 330` (compatible con Pyglet 2.0+)

  **Must NOT do**:
  - NO hardcodear la cantidad de joints (este shader es para objetos estáticos sin skinning)
  - NO añadir normal maps, occlusion, emissive (fuera de scope)
  - NO añadir múltiples luces (una luz direccional es suficiente)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Escribir 2 archivos GLSL con patrones conocidos (Phong estándar)
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5, 6)
  - **Blocks**: Tasks 7, 11, 12
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References** (existing code to follow):
  - `examples/skinning/fragment_program.glsl` — Patrón de iluminación ambient+diffuse existente. Extender con specular (Phong) y niebla.
  - `examples/skinning/vertex_program_lbs.glsl:12-26` — Estructura de inputs/outputs del vertex shader (position, normal, uv → world_position, world_normal, frag_uv)

  **API/Type References** (contracts to implement against):
  - `grafica/scenegraph.py:render()` — El Scenegraph pasa estos uniforms: `view` (mat4), `transform` (mat4), `projection` (via global_attributes), y texturas (`diffuse` en GL_TEXTURE0). Los uniforms adicionales (light_direction, camera_position, fog_color, etc.) se pasan via `set_global_attributes()` o `apply_instance_attributes()`.
  - `grafica/scenegraph.py:view_parameter_name = 'view'` y `transform_parameter_name = 'transform'` — nombres exactos de uniforms esperados

  **External References**:
  - Phong reflection model: `https://en.wikipedia.org/wiki/Phong_reflection_model` — fórmulas ambient/diffuse/specular

  **WHY Each Reference Matters**:
  - `examples/skinning/fragment_program.glsl`: Muestra el patrón exacto de iluminación que ya funciona en este repo. Solo hay que añadir specular + fog.
  - `grafica/scenegraph.py:render()`: Define qué uniforms el Scenegraph inyecta automáticamente vs cuáles hay que pasar manualmente.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Shaders tienen sintaxis GLSL válida
    Tool: Bash (grep)
    Preconditions: Archivos phong_vertex.glsl y phong_fragment.glsl existen en 21004082-K/shaders/
    Steps:
      1. grep -c "#version 330" 21004082-K/shaders/phong_vertex.glsl → 1
      2. grep -c "#version 330" 21004082-K/shaders/phong_fragment.glsl → 1
      3. grep "void main" 21004082-K/shaders/phong_vertex.glsl → encuentra "void main()"
      4. grep "void main" 21004082-K/shaders/phong_fragment.glsl → encuentra "void main()"
      5. grep "gl_Position" 21004082-K/shaders/phong_vertex.glsl → encuentra assignment a gl_Position
      6. grep "out vec4" 21004082-K/shaders/phong_fragment.glsl → encuentra output de color
    Expected Result: Todos los greps encuentran coincidencias
    Failure Indicators: Algún grep no encuentra nada → shader incompleto
    Evidence: .omo/evidence/task-1-shader-syntax.txt

  Scenario: Fragment shader incluye Phong completo (ambient + diffuse + specular + fog)
    Tool: Bash (grep)
    Preconditions: phong_fragment.glsl existe
    Steps:
      1. grep -i "ambient" 21004082-K/shaders/phong_fragment.glsl → encuentra ambient_strength
      2. grep -i "diffuse" 21004082-K/shaders/phong_fragment.glsl → encuentra dot(normal, light) o similar
      3. grep -i "specular" 21004082-K/shaders/phong_fragment.glsl → encuentra reflect o pow con shininess
      4. grep -i "fog" 21004082-K/shaders/phong_fragment.glsl → encuentra fog_color o fog_factor
    Expected Result: Los 4 componentes presentes (ambient, diffuse, specular, fog)
    Failure Indicators: Falta specular o fog → shader Phong incompleto
    Evidence: .omo/evidence/task-1-phong-components.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(aang-scene): add Phong vertex+fragment shaders for static objects`
  - Files: `21004082-K/shaders/phong_vertex.glsl`, `21004082-K/shaders/phong_fragment.glsl`

- [x] 2. Skinning LBS + Phong Shaders para Aang (330 joints)

  **What to do**:
  - Crear `21004082-K/shaders/skinning_lbs_vertex.glsl`: adaptar `examples/skinning/vertex_program_lbs.glsl`:
    - Cambiar `uniform mat4 skin_matrices[91]` → `uniform mat4 skin_matrices[330]` (Aang tiene 330 joints)
    - Inputs: position, normal, uv, joints (vec4), weights (vec4)
    - LBS: `skin_matrix = weights.x * skin_matrices[int(joints.x)] + ...` (4 influencias)
    - Outputs: world_position, world_normal, frag_uv
    - Mantener el cálculo de normal matrix: `transpose(inverse(mat3(transform) * mat3(skin_matrix)))`
  - Crear `21004082-K/shaders/skinning_phong_fragment.glsl`: copiar `phong_fragment.glsl` del Task 1 (misma lógica Phong+fog) pero añadir soporte para `alpha_cutoff` (transparencia en partes del modelo si es necesario):
    - `uniform float alpha_cutoff` — descartar pixeles con alpha < cutoff
    - `if (sampled.a < alpha_cutoff) discard;`
  - Usar `#version 330`

  **Must NOT do**:
  - NO usar DQS (Dual Quaternion Skinning) — LBS es suficiente para respiración + capa
  - NO hardcodear 91 joints — debe ser 330
  - NO añadir morph targets (no soportado por GltfModel)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Adaptar shader existente (cambiar número de joints + copiar fragment shader)
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4, 5, 6)
  - **Blocks**: Tasks 8, 11
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References** (existing code to follow):
  - `examples/skinning/vertex_program_lbs.glsl` — Shader LBS completo (46 líneas). Copiar estructura, cambiar `[91]` → `[330]`.
  - `examples/skinning/fragment_program.glsl` — Fragment shader con ambient+diffuse+alpha_cutoff. Base para el skinning_phong_fragment.glsl.

  **API/Type References**:
  - `21004082-K/assets/avatar_aang_fortnite/scene.gltf` — El modelo tiene 330 joints (verificado: `skins[0].joints` tiene 330 entradas)

  **WHY Each Reference Matters**:
  - `examples/skinning/vertex_program_lbs.glsl`: Es el shader LBS que ya funciona en este repo. Solo necesita el ajuste de joint count.
  - El conteo de 330 joints: Es crítico — si el shader dice `[91]` y el modelo tiene 330, el rendering fallará.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Shader LBS tiene 330 joints
    Tool: Bash (grep)
    Preconditions: skinning_lbs_vertex.glsl existe
    Steps:
      1. grep "skin_matrices\[330\]" 21004082-K/shaders/skinning_lbs_vertex.glsl → encuentra la declaración
      2. grep "skin_matrices\[91\]" 21004082-K/shaders/skinning_lbs_vertex.glsl → NO encuentra (el viejo valor no debe quedar)
      3. grep "weights.x \* skin_matrices" 21004082-K/shaders/skinning_lbs_vertex.glsl → encuentra la fórmula LBS
    Expected Result: 330 joints declarados, fórmula LBS presente, 91 no presente
    Failure Indicators: Sigue diciendo 91 o no tiene la fórmula LBS
    Evidence: .omo/evidence/task-2-lbs-joints.txt

  Scenario: Fragment shader tiene Phong + alpha_cutoff
    Tool: Bash (grep)
    Preconditions: skinning_phong_fragment.glsl existe
    Steps:
      1. grep "alpha_cutoff" 21004082-K/shaders/skinning_phong_fragment.glsl → encuentra el uniform + el discard
      2. grep -i "specular" 21004082-K/shaders/skinning_phong_fragment.glsl → encuentra componente specular
      3. grep -i "fog" 21004082-K/shaders/skinning_phong_fragment.glsl → encuentra niebla
    Expected Result: alpha_cutoff + Phong completo presente
    Failure Indicators: Falta alpha_cutoff o specular
    Evidence: .omo/evidence/task-2-skinning-fragment.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(aang-scene): add LBS skinning vertex shader (330 joints) + Phong fragment for Aang`
  - Files: `21004082-K/shaders/skinning_lbs_vertex.glsl`, `21004082-K/shaders/skinning_phong_fragment.glsl`

- [x] 3. Shaders de Partículas 3D (vertex + fragment GLSL)

  **What to do**:
  - Crear `21004082-K/shaders/particle_vertex.glsl`:
    - Input: `in vec3 position` (posición 3D de la partícula), `in vec4 color` (RGBA), `in float size` (tamaño del punto)
    - Uniforms: `mat4 view`, `mat4 projection`, `float point_size_scale`
    - Output: `gl_Position = projection * view * vec4(position, 1.0)`, `out vec4 frag_color`, `out float frag_depth` (profundidad para atenuación)
    - `gl_PointSize = point_size_scale * size / gl_Position.w` (atenuación por distancia — puntos lejanos más pequeños)
  - Crear `21004082-K/shaders/particle_fragment.glsl`:
    - Input: `in vec4 frag_color`, `in float frag_depth`
    - Output: `out vec4 out_color`
    - Renderizar como punto luminoso: usar `gl_PointCoord` para crear un circular soft point: `float d = length(gl_PointCoord - vec2(0.5)); if (d > 0.5) discard; float alpha = smoothstep(0.5, 0.0, d) * frag_color.a;`
    - Atenuación por profundidad: puntos lejanos más tenues: `alpha *= exp(-frag_depth * 0.01)`
    - Color final: `out_color = vec4(frag_color.rgb, alpha)`
  - Usar `#version 330`

  **Must NOT do**:
  - NO usar geometry shaders — usar GL_POINTS con gl_PointSize
  - NO textura de partícula — generar forma circular proceduralmente en el fragment shader

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 2 archivos GLSL cortos con patrón de puntos
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4, 5, 6)
  - **Blocks**: Task 10
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `examples/particles/` — Ejemplo de partículas del repo (si existe, revisar estructura de shader de puntos)
  - `grafica/scenegraph_premade.py:point_node()` — Usa GL_POINTS, referencia de cómo el repo maneja puntos

  **External References**:
  - GLSL gl_PointCoord: documentación de OpenGL — genera coords [0,1] dentro del punto
  - Soft particle technique: `smoothstep(0.5, 0.0, length(gl_PointCoord - 0.5))` — estándar para puntos circulares suaves

  **WHY Each Reference Matters**:
  - `gl_PointCoord` es la forma estándar de crear puntos circulares sin textura en GLSL. El executor debe entender este patrón.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Shaders de partículas tienen sintaxis válida
    Tool: Bash (grep)
    Preconditions: particle_vertex.glsl y particle_fragment.glsl existen
    Steps:
      1. grep "gl_PointSize" 21004082-K/shaders/particle_vertex.glsl → encuentra asignación
      2. grep "gl_PointCoord" 21004082-K/shaders/particle_fragment.glsl → encuentra uso
      3. grep "smoothstep" 21004082-K/shaders/particle_fragment.glsl → encuentra soft point
      4. grep "discard" 21004082-K/shaders/particle_fragment.glsl → encuentra descarte de pixeles fuera del círculo
    Expected Result: Todos los componentes de partículas presentes
    Failure Indicators: Falta gl_PointSize o gl_PointCoord
    Evidence: .omo/evidence/task-3-particle-shaders.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(aang-scene): add 3D particle shaders (soft points with depth attenuation)`
  - Files: `21004082-K/shaders/particle_vertex.glsl`, `21004082-K/shaders/particle_fragment.glsl`

- [x] 4. Controller de Cámara (Arcball + WASD + Damping + Límites)

  **What to do**:
  - Crear `21004082-K/camera.py` con una clase `LoFiCamera` que envuelve `grafica.arcball.Arcball`:
    - `__init__(self, width, height, target, initial_eye, scene_scale)`:
      - Crear Arcball interno con `np.linalg.inv(tr.lookAt(initial_eye, target, [0,1,0]))` como pose inicial
      - Guardar `target` (centro orbital = posición de Aang)
      - Definir `move_limits` (bounding box around target: ±limit_x, ±limit_z en plano horizontal, target_y fijo)
      - Inicializar `damping_target_pose` = pose actual, `damping_alpha` = 0.1 (factor de suavizado, 0=instantáneo, 1=inmóvil)
    - `on_mouse_press(x, y, button, modifiers)` → delegar a `arcball.down()` + `arcball.set_state()`
    - `on_mouse_drag(x, y, dx, dy, buttons, modifiers)` → delegar a `arcball.drag()`
    - `on_mouse_scroll(x, y, scroll_x, scroll_y)` → delegar a `arcball.scroll()`
    - `on_key_press_W/A/S/D(symbol)` → actualizar `move_target` (vector de desplazamiento en plano horizontal)
      - W: target -= forward_dir * move_speed (acerca)
      - S: target += forward_dir * move_speed (aleja)
      - A: target -= right_dir * move_speed (izquierda)
      - D: target += right_dir * move_speed (derecha)
      - Clamp target dentro de move_limits
    - `update(dt)`:
      - Aplicar damping: `self.arcball.pose = lerp(self.arcball.pose, self.damping_target_pose, 1.0 - exp(-damping_alpha * dt * 60))`
      - Actualizar `self.arcball.target` hacia `self.move_target` con lerp suave
    - `get_view_matrix()` → `np.linalg.inv(self.arcball.pose)`
    - `get_projection()` → delegar o reternar perspective pre-calculada
    - `reset()` → `self.arcball.reset()`
  - El damping hace que el movimiento del ratón se sienta "fluid and relaxing" como pide Escena.md
  - Los límites evitan que el usuario rompa la composición (no puede ir detrás del muro, no puede alejarse demasiado)

  **Must NOT do**:
  - NO modificar `grafica/arcball.py` — solo envolverlo
  - NO añadir roll (rotación alrededor del eje de visión) — innecesario para esta escena
  - NO hacer el damping tan fuerte que la cámara se sienta pegajosa — alpha=0.1 es suave

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Lógica de cámara con damping, WASD, y límites — requiere cuidado matemático
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 5, 6)
  - **Blocks**: Task 13
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `examples/skinning/__init__.py:457-464` — Patrón exacto de creación de Arcball con pose inicial, target, distance limits
  - `examples/arcball/__init__.py` — Patrón de event handlers de mouse para Arcball
  - `grafica/arcball.py:Arcball` — API completa: `down()`, `drag()`, `scroll()`, `set_state()`, `reset()`, `pose`, `target`

  **API/Type References**:
  - `grafica/transformations.py:lookAt(eye, at, up)` — Para calcular pose inicial
  - `grafica/arcball.py:STATE_ROTATE, STATE_PAN, STATE_ZOOM` — Estados para mouse buttons

  **WHY Each Reference Matters**:
  - `examples/skinning/__init__.py:457-464`: Muestra exactamente cómo crear y configurar un Arcball para un modelo GLTF con bounding box calculada.
  - `grafica/arcball.py`: Es la API que hay que envolver. El executor debe entender `pose` (camera-to-world) vs view matrix (inverse de pose).

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: LoFiCamera se instancia sin crash
    Tool: Bash (uv run python -c)
    Preconditions: camera.py existe, entorno uv activo
    Steps:
      1. uv run python -c "import sys; sys.path.insert(0, '.'); from grafica.transformations import lookAt; import numpy as np; print('lookAt OK')"
      2. uv run python -c "from grafica.arcball import Arcball; print('Arcball import OK')"
    Expected Result: Imports exitosos, sin crash
    Failure Indicators: ImportError o excepción al importar
    Evidence: .omo/evidence/task-4-camera-import.txt

  Scenario: camera.py tiene LoFiCamera con métodos requeridos
    Tool: Bash (grep)
    Preconditions: camera.py existe
    Steps:
      1. grep "class LoFiCamera" 21004082-K/camera.py → encuentra la clase
      2. grep "def on_mouse_press\|def on_mouse_drag\|def on_mouse_scroll\|def on_key_press\|def update\|def get_view_matrix" 21004082-K/camera.py → encuentra los métodos
      3. grep "damping\|lerp\|smooth" 21004082-K/camera.py → encuentra lógica de damping
      4. grep "move_limits\|clamp\|clip" 21004082-K/camera.py → encuentra límites de movimiento
    Expected Result: Clase + métodos + damping + límites presentes
    Failure Indicators: Falta damping o límites
    Evidence: .omo/evidence/task-4-camera-structure.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(aang-scene): add LoFiCamera controller (Arcball + WASD + damping + limits)`
  - Files: `21004082-K/camera.py`

- [x] 5. Sistema de Partículas 3D (Python)

  **What to do**:
  - Crear `21004082-K/particles3d.py` con una clase `ParticleSystem3D`:
    - `__init__(self, max_particles, spawn_center, spawn_radius, area_height)`:
      - Pre-asignar arrays NumPy (SoA): positions (N,3), velocities (N,3), colors (N,4), sizes (N,), ages (N,), ttls (N,), active (N,) bool
      - `spawn_center`: posición de Aang (centro de spawn)
      - `spawn_radius`: radio del área de spawn alrededor de Aang
      - `area_height`: altura hasta la que flotan antes de respawn
    - `emit(self, n)`:
      - Spawnear n partículas en posiciones aleatorias dentro de spawn_radius del spawn_center
      - Velocidades: leve componente upward (y positiva) + componentes x/z aleatorias pequeñas (patrón caótico suave)
      - Colors: pale yellow/green — interpolar entre (1.0, 0.9, 0.5, 0.8) y (0.7, 1.0, 0.5, 0.8) aleatoriamente
      - Sizes: 2.0 a 6.0 (puntos pequeños)
      - TTL: 8.0 a 15.0 segundos (flotan lentamente)
    - `update(self, dt)`:
      - Para cada partícula activa: position += velocity * dt, age += dt
      - Añadir turbulencia: velocity.x += sin(time + index) * small_amount, velocity.z += cos(time + index) * small_amount
      - Si age > ttl o position.y > spawn_center.y + area_height: marcar inactiva
      - Auto-emit nuevas partículas para mantener count activo cerca de max_particles
    - `get_gpu_data(self)`:
      - Retornar arrays planos (positions_flat, colors_flat, sizes_flat) para subir a vertex_list
      - Filtrar solo partículas activas
    - `draw_count(self)` → número de partículas activas
  - Inspirarse en `grafica/particle.py:ParticleSystem` (patrón SoA, Verlet/Euler) pero adaptado a 3D

  **Must NOT do**:
  - NO modificar `grafica/particle.py` — crear módulo nuevo
  - NO usar 2D (dims=3 siempre)
  - NO añadir colisiones — las partículas atraviesan todo
  - NO añadir forces complejas — solo upward + turbulencia sutil

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Sistema de partículas con arrays NumPy vectorizados, lógica de spawn/update/respawn
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4, 6)
  - **Blocks**: Task 10
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `grafica/particle.py:ParticleSystem` — Patrón SoA con NumPy, emit(), update(), positions_flat(). Adaptar de 2D a 3D.
  - `grafica/particle.py:ParticleSystem.update()` — Velocity Verlet integration pattern

  **API/Type References**:
  - `grafica/particle.py:ParticleSystem.__init__(max_particles, dims=2)` — Mismo patrón pero dims=3

  **WHY Each Reference Matters**:
  - `grafica/particle.py`: Es el sistema de partículas del repo. El executor debe seguir el mismo patrón SoA (Structure of Arrays) para consistencia, pero extendido a 3D.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: ParticleSystem3D se instancia y actualiza sin crash
    Tool: Bash (uv run python -c)
    Preconditions: particles3d.py existe
    Steps:
      1. uv run python -c "
import sys; sys.path.insert(0, '21004082-K')
from particles3d import ParticleSystem3D
import numpy as np
ps = ParticleSystem3D(max_particles=100, spawn_center=np.array([0,0,0]), spawn_radius=2.0, area_height=5.0)
ps.emit(50)
ps.update(0.016)
data = ps.get_gpu_data()
print(f'active={ps.draw_count()} positions_shape={data[0].shape}')
assert ps.draw_count() > 0, 'no active particles after emit'
print('ParticleSystem3D OK')
"
    Expected Result: "ParticleSystem3D OK" sin excepción
    Failure Indicators: Crash, draw_count()=0, o shape incorrecta
    Evidence: .omo/evidence/task-5-particles-test.txt

  Scenario: Partículas flotan hacia arriba y respawnean
    Tool: Bash (uv run python -c)
    Preconditions: particles3d.py existe
    Steps:
      1. uv run python -c "
import sys; sys.path.insert(0, '21004082-K')
from particles3d import ParticleSystem3D
import numpy as np
ps = ParticleSystem3D(max_particles=50, spawn_center=np.array([0,0,0]), spawn_radius=1.0, area_height=3.0)
ps.emit(50)
initial_y = ps.get_gpu_data()[0][1]  # y of first particle
for _ in range(100):
    ps.update(0.05)
final_data = ps.get_gpu_data()
# particles should have moved or respawned
print(f'active before=50 after={ps.draw_count()}')
assert ps.draw_count() > 0, 'all particles died'
print('Particle lifecycle OK')
"
    Expected Result: Partículas persisten después de muchos updates (respawn funciona)
    Failure Indicators: draw_count()=0 después de updates (respawn no funciona)
    Evidence: .omo/evidence/task-5-particle-lifecycle.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(aang-scene): add 3D particle system (floating spores/fireflies)`
  - Files: `21004082-K/particles3d.py`

- [x] 6. Módulo de Audio Lo-Fi (pyglet.media)

  **What to do**:
  - Crear `21004082-K/audio.py` con una función `load_lofi_audio(audio_path)`:
    - Verificar que el archivo existe (`os.path.exists`). Si no existe, print warning y retornar None (degradación graciosa)
    - Cargar con `pyglet.media.load(audio_path)`
    - Configurar como loop: `pyglet.media.Source` no tiene loop nativo, pero se puede usar `pyglet.media.Player` con `player.loop = True` o crear un `LoopingSource` wrapper que reinicia al terminar
    - Crear `pyglet.media.Player()`, encolar el source, `player.play()`
    - Retornar el player (para poder pausar/reanudar)
    - Manejar excepciones (archivo corrupto, formato no soportado) con try/except y warning
  - Añadir función `toggle_audio(player)` → pausar/reanudar
  - Añadir función `set_audio_volume(player, volume)` → ajustar volumen
  - La ruta del archivo debe ser configurable (parámetro o default a `21004082-K/assets/audio/lofi.mp3`)

  **Must NOT do**:
  - NO usar pygame.mixer u otra librería — solo pyglet.media
  - NO descargar audio de internet — el usuario provee el archivo
  - NO crash si el archivo no existe — degradación graciosa (print warning, sin audio)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Módulo simple con pyglet.media API conocida
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4, 5)
  - **Blocks**: Task 13
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `pyglet.media` API — `pyglet.media.load(path)`, `pyglet.media.Player()`, `player.queue(source)`, `player.play()`

  **External References**:
  - Pyglet docs: `https://pyglet.readthedocs.io/en/latest/programming/media.html` — API de audio, players, sources

  **WHY Each Reference Matters**:
  - `pyglet.media` es la API estándar del framework. El executor debe entender que no hay loop nativo y necesita un wrapper.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: audio.py se importa sin crash
    Tool: Bash (uv run python -c)
    Preconditions: audio.py existe
    Steps:
      1. uv run python -c "import sys; sys.path.insert(0, '21004082-K'); from audio import load_lofi_audio, toggle_audio; print('audio module OK')"
    Expected Result: "audio module OK" sin excepción
    Failure Indicators: ImportError o excepción
    Evidence: .omo/evidence/task-6-audio-import.txt

  Scenario: Degradación graciosa cuando no existe el archivo
    Tool: Bash (uv run python -c)
    Preconditions: audio.py existe, archivo de audio no existe
    Steps:
      1. uv run python -c "
import sys; sys.path.insert(0, '21004082-K')
from audio import load_lofi_audio
result = load_lofi_audio('21004082-K/assets/audio/nonexistent.mp3')
print(f'result={result}')
assert result is None, 'should return None for missing file'
print('Graceful degradation OK')
"
    Expected Result: "Graceful degradation OK" sin crash, result=None
    Failure Indicators: Crash o excepción no manejada
    Evidence: .omo/evidence/task-6-audio-degradation.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(aang-scene): add Lo-Fi audio module (pyglet.media with graceful degradation)`
  - Files: `21004082-K/audio.py`

- [x] 7. Carga de Assets GLTF + Composición de Escena (árboles, hongos, muro, arbustos, pasto)

  **What to do**:
  - Crear `21004082-K/scene_builder.py` con una función `build_scene(graph, phong_pipeline)`:
    - Cargar cada asset GLTF con `GltfModel(path)`:
      - `amanita_muscaria_mushroom/scene.gltf` → hongos (1 mesh, 1 textura)
      - `cliff_shrub_for_terrain/scene.gltf` → arbustos (1 mesh, 2 texturas)
      - `grass_claster__downoad__like_please/scene.gltf` → pasto (3 meshes, 3 texturas)
      - `realistic_trees_pack_of_2_free/scene.gltf` → árboles realistas (13 meshes, 5 texturas, 64MB — cargar selectivamente)
      - `tree grande/scene.gltf` → árbol gigante (3 meshes, 9 texturas)
    - Para cada asset: llamar `model.upload_textures()` después de tener contexto OpenGL
    - Crear vertex lists con `phong_pipeline.vertex_list_indexed(n, GL_TRIANGLES, indices)` para cada primitiva
    - Subir positions, normals, uvs a los vertex lists
    - Almacenar textura ID por primitiva (de `model.texture_gl_ids`)
    - Retornar estructura: `{"static_primitives": [...], "scene_scale": ...}` donde cada primitive dict tiene: positions, normals, uvs, indices, texture_id, transform (matriz 4x4 de placement)
  - Definir composición de escena (transforms de placement):
    - **Aang**: centro, en el origen (0, 0, 0), escalado apropiadamente
    - **Árbol gigante**: primer plano a la derecha (x=+3, y=0, z=+1), escalado grande, rotación leve para enmarcar
    - **Hongos (amanita)**: 3-5 instancias sobre la corteza del árbol gigante, apuntando hacia el centro (rotación hacia -x)
    - **Muro de roca púrpura**: detrás de Aang (z=-2), spanning horizontal (escala x ancha, escala y media). NOTA: no hay asset de muro de roca en los glTF → usar una primitiva plana con color púrpura o reutilizar cliff_shrub como sustituto. Aclarar con color púrpura via base_color_factor.
    - **Árboles fondo multicapa**: 3-5 capas a diferentes profundidades (z=-5, z=-8, z=-12, z=-16), distribuidos en x, escalados variados para parallax
    - **Arbustos**: detrás del muro de roca (z=-3 a z=-4), distribuidos, varios instancias
    - **Pasto (grass)**: alrededor de Aang en el suelo (y=0), distribuido en círculo
  - La función debe retornar también información de bounding box para configurar la cámara

  **Must NOT do**:
  - NO cargar Aang en esta tarea (Task 8 se encarga) — solo objetos estáticos
  - NO usar `Scenegraph.load_and_register_mesh()` para GLTF — usa `GltfModel` directamente (siguiendo patrón de examples/skinning/)
  - NO hardcodear más de ~20 instancias de árboles (rendimiento)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Carga múltiple de GLTF, composición de escena con transforms, manejo de texturas
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 8, 9, 10, 11, 12)
  - **Blocks**: Task 13
  - **Blocked By**: Task 1 (Phong shaders needed to create vertex lists)

  **References**:

  **Pattern References**:
  - `examples/skinning/__init__.py:328-411` — Patrón de carga de GLTF, build de Scenegraph con nodos, gather_primitives, make_vertex_list, textura handling
  - `examples/skinning/__init__.py:347-393` — gather_skinned_primitives + texture loading pattern (adaptar para static meshes: sin joints/weights)

  **API/Type References**:
  - `grafica/gltf.py:GltfModel` — Loader: `__init__(path)`, `upload_textures()`, `nodes`, `meshes`, `materials`, `texture_gl_ids`
  - `grafica/gltf.py:GltfPrimitive` — `positions, normals, uvs, colors, indices, material_index`
  - `grafica/textures.py:texture_2D_setup()` — Para textura fallback blanca

  **Asset Inventory** (verificado):
  - `amanita_muscaria_mushroom`: 3 nodes, 1 mesh, 0 skins, 1 material, 1 texture
  - `cliff_shrub_for_terrain`: 5 nodes, 1 mesh, 0 skins, 1 material, 2 textures
  - `grass_claster`: 15 nodes, 3 meshes, 0 skins, 3 materials, 3 textures
  - `realistic_trees_pack_of_2_free`: 20 nodes, 13 meshes, 0 skins, 2 materials, 5 textures (64MB!)
  - `tree grande`: 9 nodes, 3 meshes, 0 skins, 3 materials, 9 textures

  **WHY Each Reference Matters**:
  - `examples/skinning/__init__.py:328-411`: Muestra exactamente cómo cargar un GLTF, crear vertex lists con un pipeline, y manejar texturas. El patrón es el mismo para assets estáticos (solo sin joints/weights).
  - Asset inventory: El executor necesita saber cuántos meshes/texturas tiene cada asset para iterar correctamente.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: scene_builder.py se importa sin crash
    Tool: Bash (uv run python -c)
    Preconditions: scene_builder.py existe, Task 1 completado
    Steps:
      1. uv run python -c "import sys; sys.path.insert(0, '21004082-K'); from scene_builder import build_scene; print('scene_builder OK')"
    Expected Result: "scene_builder OK" sin excepción
    Failure Indicators: ImportError
    Evidence: .omo/evidence/task-7-scene-builder-import.txt

  Scenario: Assets GLTF cargan sin crash
    Tool: Bash (uv run python -c)
    Preconditions: scene_builder.py existe
    Steps:
      1. uv run python -c "
from grafica.gltf import GltfModel
import os
assets_dir = '21004082-K/assets'
for d in os.listdir(assets_dir):
    p = os.path.join(assets_dir, d, 'scene.gltf')
    if os.path.exists(p):
        m = GltfModel(p)
        print(f'{d}: meshes={len(m.meshes)} textures={len(m.texture_gl_ids) if hasattr(m, \"texture_gl_ids\") else \"N/A\"}')
print('All assets loaded OK')
"
    Expected Result: "All assets loaded OK" — cada asset carga sin crash
    Failure Indicators: Crash al cargar algún GLTF
    Evidence: .omo/evidence/task-7-asset-loading.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(aang-scene): add GLTF asset loading + scene composition (trees, mushrooms, wall, bushes, grass)`
  - Files: `21004082-K/scene_builder.py`

- [x] 8. Integración de Skinning de Aang (carga modelo, grafo de joints, skin matrices, vertex lists)

  **What to do**:
  - Crear `21004082-K/aang.py` con función `setup_aang(model_path, skinning_pipeline)`:
    - Cargar `GltfModel(model_path)` para `avatar_aang_fortnite/scene.gltf`
    - Encontrar el skin: iterar `model.nodes` buscando `node.skin_index is not None`
    - Verificar que el skin tiene 330 joints
    - Construir Scenegraph con todos los nodos del GLTF como transform nodes:
      - `graph.add_transform(name, node.local_matrix())` para cada nodo
      - `graph.add_edge(parent, child)` según jerarquía de `node.children`
      - Conectar roots a "root" del Scenegraph
    - Gather skinned primitives (siguiendo `examples/skinning/gather_skinned_primitives()`)
    - Crear vertex lists con `skinning_pipeline.vertex_list_indexed()`:
      - Subir positions, normals, uvs, joints (vec4), weights (vec4)
    - Cargar texturas: `model.upload_textures()` + mapear materials a texture_gl_ids
    - Crear white pixel texture fallback
    - Retornar estructura: `{"model": model, "graph": graph, "primitives": [...], "node_to_scenegraph_name": [...], "n_joints": 330, "skin": mesh_skin}`
  - Añadir función `compute_skin_matrices(model, graph, node_to_scenegraph_name)` (copiar de examples/skinning/compute_skin_matrices)
  - Añadir función `compute_aang_bbox(model, graph, primitives, ...)` para encuadrar cámara (copiar compute_skinned_bbox del ejemplo)

  **Must NOT do**:
  - NO animar joints en esta tarea (Task 9) — solo setup estático
  - NO usar DQS — solo LBS
  - NO modificar el shader (Task 2 ya lo hizo)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Integración compleja de skinning: GLTF parsing, Scenegraph construction, skin matrix computation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 9, 10, 11, 12)
  - **Blocks**: Tasks 9, 10, 13
  - **Blocked By**: Task 2 (skinning shaders needed to create vertex lists)

  **References**:

  **Pattern References**:
  - `examples/skinning/__init__.py:268-411` — Patrón COMPLETO de carga de GLTF con skinning: GltfModel, find skin, build Scenegraph, gather_primitives, make_vertex_list, texture loading. COPIAR y adaptar.
  - `examples/skinning/__init__.py:168-195` — `compute_skin_matrices()`: calcula skin_matrices, real_quats, dual_quats desde global transforms × inverse bind matrices
  - `examples/skinning/__init__.py:198-221` — `compute_skinned_bbox()`: calcula bounding box en pose actual aplicando skinning en CPU
  - `examples/skinning/__init__.py:224-265` — `gather_skinned_primitives()`: recolecta primitivas con joints/weights

  **API/Type References**:
  - `grafica/gltf.py:GltfModel` — `nodes`, `skins`, `meshes`, `materials`, `texture_gl_ids`, `upload_textures()`
  - `grafica/gltf.py:GltfSkin` — `joints` (lista de indices), `inverse_bind_matrices` (array N×4×4), `skeleton_root`
  - `grafica/gltf.py:GltfNode` — `local_matrix()`, `children`, `skin_index`, `mesh_index`
  - `grafica/gltf.py:_compose_trs(translation, rotation, scale)` — Para componer matrices TRS al aplicar animación

  **WHY Each Reference Matters**:
  - `examples/skinning/__init__.py:268-411`: Es el código de referencia exacto. El executor debe copiar este patrón y adaptar para Aang (330 joints, 2 meshes, 2 materials).
  - `compute_skin_matrices`: Esta función es crítica — calcula las matrices que el shader LBS usa. Sin esto, el skinning no funciona.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Aang GLTF carga con 330 joints
    Tool: Bash (uv run python -c)
    Preconditions: aang.py existe
    Steps:
      1. uv run python -c "
from grafica.gltf import GltfModel
m = GltfModel('21004082-K/assets/avatar_aang_fortnite/scene.gltf')
skin_idx = None
for n in m.nodes:
    if n.skin_index is not None:
        skin_idx = n.skin_index
        break
assert skin_idx is not None, 'no skin found'
n_joints = len(m.skins[skin_idx].joints)
print(f'joints={n_joints}')
assert n_joints == 330, f'expected 330 joints, got {n_joints}'
print('Aang skin OK')
"
    Expected Result: "Aang skin OK", joints=330
    Failure Indicators: joints != 330 o crash
    Evidence: .omo/evidence/task-8-aang-skin.txt

  Scenario: aang.py se importa y setup_aang retorna estructura válida
    Tool: Bash (uv run python -c)
    Preconditions: aang.py existe, Task 2 completado
    Steps:
      1. uv run python -c "import sys; sys.path.insert(0, '21004082-K'); from aang import setup_aang, compute_skin_matrices; print('aang module OK')"
    Expected Result: "aang module OK" sin excepción
    Failure Indicators: ImportError
    Evidence: .omo/evidence/task-8-aang-module.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(aang-scene): add Aang skinning integration (LBS, 330 joints, GLTF loading)`
  - Files: `21004082-K/aang.py`

- [x] 9. Animación de Aang: Respiración + Viento en Capa

  **What to do**:
  - En `21004082-K/aang.py`, añadir función `apply_breathing_and_wind(model, graph, node_to_scenegraph_name, time)`:
    - **Respiración**: identificar joints del spine (nodos con nombre que contiene "spine" o "Spine" — del glTF: spine_01_06, spine_02_07, spine_03_08, spine_04_09, spine_05_010, indices 8-12)
      - Para cada spine joint: aplicar rotación leve sinusoidal alrededor del eje X (inflar/desinflar pecho)
      - Amplitud: ~0.02 radianes (muy sutil), frecuencia: ~0.5 Hz (ciclo de 2 segundos — respiración lenta y meditativa)
      - `breath = 0.02 * sin(2 * pi * 0.5 * time)`
      - Modificar el transform del joint: `graph.nodes[name]["transform"] = base_transform @ tr.rotationX(breath)`
      - Guardar base_transform al inicio (no acumular la rotación cada frame)
    - **Viento en capa**: identificar joints de la cape (nodos con nombre que contiene "cape" — cape_012 (index 14), cape_0_013 (index 16), cape_0_end_0229, cape_end_0228)
      - Para cada cape joint: aplicar rotación sinusoidal alrededor de Z o Y (ondulación)
      - Amplitud: ~0.05-0.1 radianes, frecuencia: ~0.3 Hz (viento lento)
      - `wind = 0.08 * sin(2 * pi * 0.3 * time + phase_offset_per_joint)` — phase_offset diferente por joint para crear onda
      - Modificar el transform del joint de la cape
    - **Cabeza**: ligera inclinación hacia abajo (estático, no animado): aplicar rotación X negativa al joint del head (head_016, index 20) una sola vez al inicio
    - La función debe llamarse cada frame en el update loop

  **Must NOT do**:
  - NO reponer a lotus (solo respiración + capa)
  - NO usar animaciones pre-empaquetadas (el modelo no tiene) — animación procedural sinusoidal
  - NO acumular rotación cada frame (sobrescribir desde base_transform, no multiplicar acumulativamente)
  - NO animar todos los 330 joints — solo spine + cape + head

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Identificar joints por nombre, animación procedural sinusoidal, cuidado de no acumular transforms
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 10, 11, 12)
  - **Blocks**: Task 13
  - **Blocked By**: Task 8 (Aang setup needed)

  **References**:

  **Pattern References**:
  - `examples/skinning/__init__.py:504-515` — `apply_animation_to_graph()`: patrón de aplicar overrides a nodos del Scenegraph. Adaptar: en lugar de `model.sample_animation()`, generar transforms sinusoidales.
  - `grafica/gltf.py:_compose_trs(translation, rotation, scale)` — Para componer transforms modificados

  **API/Type References**:
  - Aang glTF node names (verificado):
    - Spine: `spine_01_06` (idx 8), `spine_02_07` (idx 9), `spine_03_08` (idx 10), `spine_04_09` (idx 11), `spine_05_010` (idx 12)
    - Cape: `cape_012` (idx 14), `cape_0_013` (idx 16), `cape_end_0228` (idx 15), `cape_0_end_0229` (idx 17)
    - Head: `head_016` (idx 20)
  - `grafica/transformations.py:rotationX(theta)`, `rotationY(theta)`, `rotationZ(theta)` — Para crear rotaciones de animación

  **WHY Each Reference Matters**:
  - `examples/skinning/__init__.py:504-515`: Muestra cómo modificar transforms de nodos del Scenegraph cada frame. El patrón es: `graph.nodes[node_name]["transform"] = new_matrix`.
  - Aang joint names: El executor necesita saber exactamente qué nodos animar. Sin esto, tendría que inspeccionar el glTF manualmente.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: apply_breathing_and_wind modifica transforms de joints correctos
    Tool: Bash (uv run python -c)
    Preconditions: aang.py con apply_breathing_and_wind existe
    Steps:
      1. uv run python -c "
import sys; sys.path.insert(0, '21004082-K')
from aang import apply_breathing_and_wind
import inspect
src = inspect.getsource(apply_breathing_and_wind)
# Verify it references spine and cape joints
assert 'spine' in src.lower() or 'Spine' in src, 'no spine joint animation'
assert 'cape' in src.lower() or 'Cape' in src, 'no cape joint animation'
assert 'sin' in src, 'no sinusoidal animation'
print('Breathing + wind animation structure OK')
"
    Expected Result: "Breathing + wind animation structure OK"
    Failure Indicators: Falta spine, cape, o sin
    Evidence: .omo/evidence/task-9-animation-structure.txt

  Scenario: Animación no acumula transforms (sobrescribe desde base)
    Tool: Bash (grep)
    Preconditions: aang.py existe
    Steps:
      1. grep -i "base_transform\|original_transform\|initial_transform\|bind\|reset" 21004082-K/aang.py → encuentra referencia a transform base
    Expected Result: Encuentra patrón que guarda/restaura transform base
    Failure Indicators: No hay base_transform → la animación acumularía rotación indefinidamente
    Evidence: .omo/evidence/task-9-no-accumulate.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(aang-scene): add Aang breathing + cape wind animation (procedural sinusoidal joint animation)`
  - Files: `21004082-K/aang.py` (edited)

- [x] 10. Integración de Partículas (spawn, render, update)

  **What to do**:
  - En `21004082-K/particles3d.py` (o un nuevo `21004082-K/particle_renderer.py`), añadir:
    - Función `setup_particle_renderer(particle_pipeline, max_particles)`:
      - Crear un `vertex_list` dinámico con `particle_pipeline.vertex_list(max_particles, GL_POINTS)`:
        - Atributos: position (vec3), color (vec4), size (float)
      - Retornar `{"pipeline": particle_pipeline, "vertex_list": vl, "max_particles": max_particles}`
    - Función `render_particles(renderer, particle_system, view, projection)`:
      - Obtener GPU data de `particle_system.get_gpu_data()`
      - Actualizar vertex_list: `vl.position[:] = positions_flat`, `vl.color[:] = colors_flat`, `vl.size[:] = sizes_flat`
      - `pipeline.use()`, set uniforms (view, projection, point_size_scale)
      - `vl.draw(GL_POINTS, count=particle_system.draw_count())`
    - El spawn_center debe ser la posición de Aang (pasada como parámetro)
    - El spawn_radius: ~2-3 unidades alrededor de Aang
    - El area_height: ~5-6 unidades (las partículas flotan hasta esa altura antes de respawn)

  **Must NOT do**:
  - NO usar GL_TRIANGLES para partículas — usar GL_POINTS
  - NO crear más de 200 partículas (rendimiento)
  - NO hacer las partículas demasiado brillantes (pálidas, amarillo/verde sutil)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Integración de sistema de partículas con pipeline de render, vertex lists dinámicos
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9, 11, 12)
  - **Blocks**: Task 13
  - **Blocked By**: Tasks 3 (particle shaders), 5 (particle system), 8 (Aang position needed for spawn center)

  **References**:

  **Pattern References**:
  - `examples/skinning/__init__.py:397-411` — `make_vertex_list()`: patrón de crear vertex_list con pipeline. Adaptar para GL_POINTS (no indexed).
  - `examples/skinning/__init__.py:573-581` — Patrón de draw loop: `pipeline.use()`, set uniforms, `vl.draw()`.

  **API/Type References**:
  - `grafica/utils.py:load_pipeline(vertex_path, fragment_path)` — Para cargar el particle shader
  - `21004082-K/particles3d.py:ParticleSystem3D` — Sistema creado en Task 5
  - `21004082-K/shaders/particle_vertex.glsl` — Shader creado en Task 3

  **WHY Each Reference Matters**:
  - `examples/skinning/__init__.py:397-411`: Muestra cómo crear vertex lists con un pipeline específico. El patrón es el mismo para partículas, solo que GL_POINTS sin indices.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: setup_particle_renderer y render_particles existen
    Tool: Bash (grep)
    Preconditions: particles3d.py o particle_renderer.py existe
    Steps:
      1. grep "def setup_particle_renderer\|def render_particles" 21004082-K/particles3d.py 21004082-K/particle_renderer.py 2>/dev/null → encuentra ambas funciones
      2. grep "GL_POINTS" 21004082-K/particles3d.py 21004082-K/particle_renderer.py 2>/dev/null → encuentra uso de GL_POINTS
    Expected Result: Funciones presentes, usa GL_POINTS
    Failure Indicators: Funciones faltantes o usa GL_TRIANGLES
    Evidence: .omo/evidence/task-10-particle-renderer.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(aang-scene): integrate 3D particle rendering (spawn around Aang, float upward, respawn)`
  - Files: `21004082-K/particles3d.py` (edited) or `21004082-K/particle_renderer.py`

- [x] 11. Integración de Niebla en Shaders Phong

  **What to do**:
  - Verificar que `phong_fragment.glsl` (Task 1) y `skinning_phong_fragment.glsl` (Task 2) ya incluyen niebla por distancia. Si no, añadirla:
    - En ambos fragment shaders, añadir/nomralizar:
      - `uniform vec4 fog_color` (color verde-amarillento: ~vec4(0.6, 0.7, 0.3, 1.0))
      - `uniform float fog_near` (distancia cercana donde la niebla empieza: ~10.0)
      - `uniform float fog_far` (distancia lejana donde la niebla es total: ~30.0)
    - En el main del fragment shader, después de calcular `phong_color`:
      - `float depth = length(world_position - camera_position);`
      - `float fog_factor = clamp(smoothstep(fog_near, fog_far, depth), 0.0, 1.0);`
      - `out_color = vec4(mix(phong_color, fog_color.rgb, fog_factor), phong_alpha);`
  - Asegurar que `camera_position` esté disponible como uniform en ambos shaders (pasado desde el código Python)
  - Crear un pequeño helper o documentación sobre cómo pasar los uniforms de fog desde Python: via `pipeline["fog_color"]`, `pipeline["fog_near"]`, `pipeline["fog_far"]`, `pipeline["camera_position"]`

  **Must NOT do**:
  - NO usar raymarching para niebla volumétrica — solo niebla por distancia (smoothstep)
  - NO añadir niebla a las partículas (ellas tienen su propia atenuación por profundidad)
  - NO hacer la niebla demasiado densa (debe ser sutil, atmosférica)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Editar 2 archivos GLSL existentes para añadir/verificar niebla
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9, 10, 12)
  - **Blocks**: Task 13
  - **Blocked By**: Tasks 1, 2 (shaders must exist first)

  **References**:

  **Pattern References**:
  - `21004082-K/shaders/phong_fragment.glsl` (Task 1) — Debería ya tener fog. Verificar/completar.
  - `21004082-K/shaders/skinning_phong_fragment.glsl` (Task 2) — Debería ya tener fog. Verificar/completar.

  **WHY Each Reference Matters**:
  - Los shaders del Task 1 y 2 deberían incluir niebla desde el inicio. Esta tarea es de verificación y completitud.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Niebla presente en ambos fragment shaders
    Tool: Bash (grep)
    Preconditions: Tasks 1 y 2 completados
    Steps:
      1. grep -i "fog_color\|fog_near\|fog_far\|fog_factor\|fog_density" 21004082-K/shaders/phong_fragment.glsl → encuentra niebla
      2. grep -i "fog_color\|fog_near\|fog_far\|fog_factor\|fog_density" 21004082-K/shaders/skinning_phong_fragment.glsl → encuentra niebla
      3. grep "smoothstep\|mix" 21004082-K/shaders/phong_fragment.glsl → encuentra la mezcla de niebla
      4. grep "smoothstep\|mix" 21004082-K/shaders/skinning_phong_fragment.glsl → encuentra la mezcla de niebla
    Expected Result: Niebla presente en ambos shaders con smoothstep/mix
    Failure Indicators: Falta niebla en algún shader
    Evidence: .omo/evidence/task-11-fog-verification.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(aang-scene): verify/complete distance-based fog in Phong + skinning fragment shaders`
  - Files: `21004082-K/shaders/phong_fragment.glsl` (edited), `21004082-K/shaders/skinning_phong_fragment.glsl` (edited)

- [x] 12. Configuración de Fondo + Iluminación

  **What to do**:
  - Crear o añadir a `21004082-K/scene_builder.py` función `get_lighting_config()`:
    - Retornar dict con:
      - `light_direction`: `np.array([0.4, 0.7, 0.5], dtype=np.float32)` (luz desde arriba-derecha-frontal, direccional)
      - `light_color`: `np.array([1.0, 0.95, 0.8], dtype=np.float32)` (luz cálida, tono Lo-Fi)
      - `ambient_strength`: `0.35` (ambiente moderado, atmósfera suave)
      - `shininess`: `32.0` (specular Phong, moderado)
      - `fog_color`: `np.array([0.6, 0.7, 0.3, 1.0], dtype=np.float32)` (verde-amarillento, místico)
      - `fog_near`: `10.0`
      - `fog_far`: `30.0`
      - `background_bottom_color`: `(0.05, 0.08, 0.15)` (azul oscuro, fondo atmosférico)
      - `background_top_color`: `(0.15, 0.12, 0.08)` (marrón verdoso, cielo bosque)
  - Crear helper `setup_lighting(pipeline, config, camera_position)`:
    - `pipeline["light_direction"] = config["light_direction"].reshape(3, 1, order="F")`
    - `pipeline["light_color"] = config["light_color"].reshape(3, 1, order="F")`
    - `pipeline["ambient_strength"] = config["ambient_strength"]`
    - `pipeline["shininess"] = config["shininess"]`
    - `pipeline["camera_position"] = camera_position.reshape(3, 1, order="F")`
    - `pipeline["fog_color"] = config["fog_color"].reshape(4, 1, order="F")`
    - `pipeline["fog_near"] = config["fog_near"]`
    - `pipeline["fog_far"] = config["fog_far"]`
  - Usar `GradientBackground` de `grafica/background.py` con los colores definidos

  **Must NOT do**:
  - NO usar colores saturados — tonos apagados, atmosféricos, Lo-Fi
  - NO añadir múltiples luces — una direccional es suficiente
  - NO hacer la luz demasiado fuerte — ambient_strength 0.35 mantiene sombras suaves

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Configuración de parámetros + helper simple de uniforms
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9, 10, 11)
  - **Blocks**: Task 13
  - **Blocked By**: Task 1 (Phong shaders define the uniforms)

  **References**:

  **Pattern References**:
  - `examples/skinning/__init__.py:468-470` — Patrón de light_direction, ambient_strength, base_color_factor
  - `grafica/background.py:GradientBackground` — Background con bottom_color, top_color

  **WHY Each Reference Matters**:
  - `examples/skinning/__init__.py:468-470`: Muestra los valores de iluminación que ya funcionan en este repo. Adaptar con tonos más cálidos/atmosféricos para Lo-Fi.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: get_lighting_config retorna dict con todos los parámetros
    Tool: Bash (uv run python -c)
    Preconditions: scene_builder.py con get_lighting_config existe
    Steps:
      1. uv run python -c "
import sys; sys.path.insert(0, '21004082-K')
from scene_builder import get_lighting_config
c = get_lighting_config()
required = ['light_direction', 'light_color', 'ambient_strength', 'shininess', 'fog_color', 'fog_near', 'fog_far']
for k in required:
    assert k in c, f'missing {k}'
print('Lighting config OK')
"
    Expected Result: "Lighting config OK" sin AssertionError
    Failure Indicators: Falta algún parámetro
    Evidence: .omo/evidence/task-12-lighting-config.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(aang-scene): add lighting config + background setup (warm Lo-Fi tones, green-yellow fog)`
  - Files: `21004082-K/scene_builder.py` (edited)

- [x] 13. Punto de Entrada Principal: tarea() — Window, Wire Everything, Event Handlers, Draw Loop

  **What to do**:
  - Reescribir `21004082-K/__init__.py` para reemplazar el placeholder "¡Hola, CC3501!" con la escena 3D completa:
    - Mantener el `@click.command("tarea")` con `--width`/`--height` options
    - En el body de `tarea(width, height)`:
      1. **Window setup**: `window = pyglet.window.Window(width, height, caption="Aang Meditando — Lo-Fi")`
      2. **GL state**: `GL.glEnable(GL.GL_DEPTH_TEST)`, `GL.glEnable(GL.GL_BLEND)`, `GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)`
      3. **Font**: cargar FiraCode
      4. **Load pipelines**:
         - `phong_pipeline = load_pipeline(shaders/phong_vertex.glsl, shaders/phong_fragment.glsl)`
         - `skinning_pipeline = load_pipeline(shaders/skinning_lbs_vertex.glsl, shaders/skinning_phong_fragment.glsl)`
         - `particle_pipeline = load_pipeline(shaders/particle_vertex.glsl, shaders/particle_fragment.glsl)`
      5. **Setup scene** (call functions from previous tasks):
         - `lighting = get_lighting_config()`
         - `static_data = build_scene(graph, phong_pipeline)` (from Task 7)
         - `aang_data = setup_aang(aang_path, skinning_pipeline)` (from Task 8)
         - `particle_system = ParticleSystem3D(...)` (from Task 5)
         - `particle_renderer = setup_particle_renderer(particle_pipeline, 150)` (from Task 10)
         - `background = GradientBackground(bottom, top)` (from Task 12)
      6. **Camera setup**:
         - Calcular bounding box de Aang (compute_aang_bbox)
         - `camera = LoFiCamera(width, height, target=center, initial_eye=center+offset, scene_scale=diagonal)`
         - `projection = tr.perspective(45, width/height, near, far)`
      7. **Audio setup**: `audio_player = load_lofi_audio(audio_path)` (from Task 6)
      8. **Skin matrices buffer** (pre-allocate, like examples/skinning):
         - `Mat4Array = (GLfloat * 16) * 330`
         - `skin_matrices_buffer = Mat4Array()`
         - `skin_matrices_view = np.frombuffer(skin_matrices_buffer, dtype=np.float32).reshape(330, 16)`
      9. **Event handlers**:
         - `@window.event on_draw()`:
           - `window.clear()`, `background.draw()`
           - Update view: `view = camera.get_view_matrix()`, `camera_pos = -view[:3, 3]` (or extract from pose)
           - **Draw static objects** (trees, mushrooms, wall, bushes, grass):
             - `phong_pipeline.use()`
             - Set uniforms: view, projection, lighting (via setup_lighting helper), camera_position
             - For each static primitive: bind texture, set transform, draw
           - **Draw Aang** (skinning):
             - `apply_breathing_and_wind(aang_data, time)` (Task 9)
             - `skin_matrices = compute_skin_matrices(aang_data)` (Task 8)
             - `skin_matrices_view[:] = skin_matrices.transpose(0, 2, 1).reshape(330, 16)`
             - `skinning_pipeline.use()`
             - Set uniforms: view, projection, lighting, camera_position, skin_matrices_buffer, base_color_factor
             - For each Aang primitive: bind texture, draw
           - **Draw particles**:
             - `particle_system.update(dt)`, `render_particles(particle_renderer, particle_system, view, projection)`
           - **Draw HUD** (Task 14)
         - `@window.event on_mouse_press/drag/scroll` → delegate to `camera.on_mouse_*()`
         - `@window.event on_key_press`:
           - W/A/S/D → `camera.on_key_press_WASD()`
           - R → `camera.reset()`
           - SPACE → pause/resume animation
           - M → toggle audio (toggle_audio)
           - ESC → `window.close()`
      10. **Update loop**: `pyglet.clock.schedule_interval(update, 1/60.0)`:
          - `state["time"] += dt`
          - Update camera damping: `camera.update(dt)`
      11. `pyglet.app.run()`
  - Estructura del state: `{"time": 0.0, "paused": False, "audio_on": True}`

  **Must NOT do**:
  - NO modificar `__main__.py` — ya llama `tarea.callback(800, 600)` correctamente
  - NO modificar `caja_de_juguetes.py` — el comando `tarea` ya está registrado
  - NO poner toda la lógica en `__init__.py` — delegar a funciones de otros módulos
  - NO olvidar el orden: `upload_textures()` DEBE llamarse después de crear la ventana (contexto OpenGL activo)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Integración final de todos los componentes, event handlers, draw loop — el task más complejo
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (sequential, after all Wave 2 tasks)
  - **Blocks**: Task 14, F1-F4
  - **Blocked By**: Tasks 4, 5, 6, 7, 8, 9, 10, 11, 12 (ALL Wave 2 + Wave 1 dependencies)

  **References**:

  **Pattern References**:
  - `examples/skinning/__init__.py:268-667` — El ejemplo COMPLETO de skinning con Arcball + I/O + draw loop. Es la referencia principal para este task.
  - `examples/skinning/__init__.py:533-608` — on_draw() completo: background, view update, skin matrices, draw primitives, skeleton, HUD
  - `examples/skinning/__init__.py:610-666` — on_key_press, on_mouse_*, update loop, pyglet.clock.schedule_interval
  - `examples/arcball/__init__.py` — Patrón alternativo de Arcball + I/O (más simple que skinning)

  **API/Type References**:
  - `21004082-K/camera.py:LoFiCamera` — Task 4
  - `21004082-K/scene_builder.py:build_scene, get_lighting_config, setup_lighting` — Tasks 7, 12
  - `21004082-K/aang.py:setup_aang, compute_skin_matrices, apply_breathing_and_wind, compute_aang_bbox` — Tasks 8, 9
  - `21004082-K/particles3d.py:ParticleSystem3D, setup_particle_renderer, render_particles` — Tasks 5, 10
  - `21004082-K/audio.py:load_lofi_audio, toggle_audio` — Task 6
  - `grafica/background.py:GradientBackground` — Background
  - `grafica/ui.py:ui_overlay` — HUD overlay context manager
  - `grafica/utils.py:load_pipeline` — Shader loading

  **WHY Each Reference Matters**:
  - `examples/skinning/__init__.py`: Es el template más cercano a lo que hay que construir. Tiene GLTF + skinning + Arcball + draw loop + I/O + HUD. El executor debe seguir este patrón estructural.
  - Los módulos de Tasks 4-12: Son las funciones que este task llama. El executor necesita saber qué funciones existen y qué retornan.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: tarea() ejecuta sin crash y abre ventana
    Tool: Bash (uv run timeout)
    Preconditions: ALL previous tasks completed
    Steps:
      1. timeout 10 uv run python -c "
import sys
sys.path.insert(0, '.')
# Import the tarea command
import importlib
mod = importlib.import_module('21004082-K')
print('tarea command imported OK')
print('Module attrs:', [a for a in dir(mod) if not a.startswith('_')])
"
    Expected Result: "tarea command imported OK" sin excepción
    Failure Indicators: ImportError, SyntaxError, o cualquier excepción
    Evidence: .omo/evidence/task-13-tarea-import.txt

  Scenario: La escena renderiza (sin crash en runtime)
    Tool: Bash (uv run timeout + xvfb)
    Preconditions: All tasks completed, display available (xvfb or real)
    Steps:
      1. timeout 15 uv run python -c "
import pyglet
import sys
sys.path.insert(0, '.')
# Try to create window and run for a few frames
import importlib
mod = importlib.import_module('21004082-K')
# Access the click command's callback
import click
ctx = click.Context(mod.tarea)
# Run with default width/height — if it crashes, we catch it
try:
    mod.tarea.callback(800, 600)
except SystemExit:
    pass
except Exception as e:
    print(f'CRASH: {e}')
    sys.exit(1)
print('Scene ran without crash')
" 2>&1 | head -20
    Expected Result: No "CRASH" in output, or window opens and renders
    Failure Indicators: "CRASH" in output, traceback, segfault
    Evidence: .omo/evidence/task-13-scene-runtime.txt

  Scenario: Event handlers están registrados
    Tool: Bash (grep)
    Preconditions: __init__.py reescrito
    Steps:
      1. grep "on_draw" 21004082-K/__init__.py → encuentra handler
      2. grep "on_mouse_press\|on_mouse_drag\|on_mouse_scroll" 21004082-K/__init__.py → encuentra mouse handlers
      3. grep "on_key_press" 21004082-K/__init__.py → encuentra keyboard handler
      4. grep "pyglet.app.run" 21004082-K/__init__.py → encuentra el run loop
      5. grep "pyglet.clock.schedule_interval" 21004082-K/__init__.py → encuentra el update loop
    Expected Result: Todos los handlers y loops presentes
    Failure Indicators: Falta algún handler o loop
    Evidence: .omo/evidence/task-13-event-handlers.txt
  ```

  **Commit**: YES
  - Message: `feat(aang-scene): wire main entry point tarea() with full interactive 3D scene`
  - Files: `21004082-K/__init__.py` (rewritten)
  - Pre-commit: `uv run python -c "import importlib; importlib.import_module('21004082-K')"`

- [x] 14. HUD Overlay (instrucciones de controles + info)

  **What to do**:
  - En `21004082-K/__init__.py` (o un helper `21004082-K/hud.py`), añadir:
    - Crear labels de pyglet.text.Label con FiraCode:
      - Title: "Aang Meditando — Lo-Fi" (top-left, font_size=16, color amarillo cálido)
      - Controls: "WASD: mover | Mouse: orbitar | Rueda: zoom | R: reset | SPACE: pausa | M: audio | ESC: salir" (bottom-left, font_size=11, color gris claro)
      - Info: FPS counter o estado (pausa/play, audio on/off) — actualizar cada frame
    - En `on_draw()`, después de renderizar la escena 3D:
      - `with ui_overlay():` (desactiva depth test, activa blending)
      - Dibujar cada label con `.draw()`
    - Actualizar labels de info en el update loop (FPS, estado)

  **Must NOT do**:
  - NO hacer el HUD intrusivo — texto pequeño, esquinas, no obstruir la escena
  - NO añadir botones o UI interactiva — solo texto informativo
  - NO usar fuentes no disponibles — usar FiraCode (cargado en Task 13)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Añadir labels de texto y dibujarlos en el overlay
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Task 13's draw loop)
  - **Parallel Group**: Wave 3 (after Task 13)
  - **Blocks**: F1-F4
  - **Blocked By**: Task 13

  **References**:

  **Pattern References**:
  - `examples/skinning/__init__.py:484-495` — Patrón de labels con FiraCode, posicionamiento, colores
  - `examples/skinning/__init__.py:605-608` — Patrón de draw HUD con `ui_overlay()`
  - `grafica/ui.py:ui_overlay` — Context manager que desactiva depth test para UI
  - `grafica/ui.py:InfoPanel` — Panel de info alternativo (más estructurado)

  **WHY Each Reference Matters**:
  - `examples/skinning/__init__.py:484-495`: Muestra exactamente cómo crear y posicionar labels en este repo.
  - `grafica/ui.py:ui_overlay`: Es el helper que asegura que el HUD se dibuje encima de la escena 3D sin conflictos de depth.

  **Acceptance Criteria**:

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: HUD con labels de controles presentes
    Tool: Bash (grep)
    Preconditions: __init__.py con HUD completado
    Steps:
      1. grep "ui_overlay" 21004082-K/__init__.py 21004082-K/hud.py 2>/dev/null → encuentra uso de ui_overlay
      2. grep "WASD\|Mouse\|reset\|pausa\|audio\|ESC" 21004082-K/__init__.py 21004082-K/hud.py 2>/dev/null → encuentra texto de controles
      3. grep "Label" 21004082-K/__init__.py 21004082-K/hud.py 2>/dev/null → encuentra creación de labels
    Expected Result: ui_overlay + labels + texto de controles presentes
    Failure Indicators: Falta ui_overlay o labels
    Evidence: .omo/evidence/task-14-hud.txt
  ```

  **Commit**: YES (groups with Wave 3)
  - Message: `feat(aang-scene): add HUD overlay with controls help and scene info`
  - Files: `21004082-K/__init__.py` (edited) or `21004082-K/hud.py`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .omo/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `uv run ruff check .` (if available). Review all changed files for: empty catches, print en prod (except debug), commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names (data/result/item/temp). Verify all GLSL shaders compile (no syntax errors). Verify Python modules import without crash.
  Output: `Lint [PASS/FAIL] | Shaders [N/N compile] | Imports [N/N ok] | Files [N clean/N issues] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high`
  Start from clean state. Run `uv run python caja_de_juguetes.py tarea`. Verify: window opens, scene renders, Aang visible with skinning, trees/mushrooms/wall visible, particles floating, fog visible, mouse rotates camera, WASD moves camera, audio plays (or degrades gracefully). Test edge cases: resize window, press ESC, press R (reset). Save screenshots to `.omo/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance: no modifications to grafica/, no cloth physics, no DoF, no lotus reposing, no automated tests. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1**: `feat(aang-scene): add Phong, skinning, particle shaders + camera/audio/particle utilities` — shaders/*.glsl, camera.py, particles3d.py, audio.py
- **Wave 2**: `feat(aang-scene): add scene composition, Aang skinning integration, animations, fog` — scene_builder.py, aang.py, shader edits
- **Wave 3**: `feat(aang-scene): wire main entry point tarea() with full interactive scene` — __init__.py, HUD
- **Final**: `feat(aang-scene): complete Lo-Fi meditation scene with all elements` — any remaining fixes

---

## Success Criteria

### Verification Commands
```bash
# Run the scene
uv run python caja_de_juguetes.py tarea
# Expected: window opens, 3D scene renders, no crash

# Verify Aang model loads
uv run python -c "from grafica.gltf import GltfModel; m = GltfModel('21004082-K/assets/avatar_aang_fortnite/scene.gltf'); print(f'joints={len(m.skins[0].joints)} meshes={len(m.meshes)}')"
# Expected: joints=330 meshes=2

# Verify all shaders have no obvious syntax issues
grep -r "void main" 21004082-K/shaders/
# Expected: 6+ matches (vertex + fragment for each pipeline)

# Verify all Python modules import
uv run python -c "from 21004082_K import tarea; print('OK')"
# Expected: OK (or imports successfully)
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] `uv run python caja_de_juguetes.py tarea` runs without crash
- [ ] Scene renders Aang with skinning
- [ ] Scene renders environment (trees, mushrooms, wall, bushes)
- [ ] Particles visible floating upward
- [ ] Fog visible in background
- [ ] Camera responds to mouse (orbit) and WASD (move)
- [ ] Audio plays in loop (or degrades gracefully)
