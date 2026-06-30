# Escena Cinematográfica Zuko vs Ozai — Implementación 3D

## TL;DR

> **Quick Summary**: Implementar una escena cinematográfica 3D de 28 segundos (7 planos) de la confrontación Zuko vs Ozai (Avatar), usando la librería grafica/ del repositorio con Scenegraph, shaders de iluminación multiple_lights, modelos 3D externos con fallback a primitivas, reproducción automática temporizada, y personajes articulados.
>
> **Deliverables**:
> - Paquete `21004082-K/` completo con __init__.py, shaders GLSL, y assets
> - Personajes articulados (Zuko y Ozai) con modelo jerárquico
> - Escenario detallado: trono, pilares, antorchas, paredes, suelo
> - Sistema de iluminación cálida (1 PointLight + 2 SpotLights, tonos naranja/rojo)
> - Timeline de 7 planos cinematográficos con cámara y animación
> - Controles de teclado (pausar, reiniciar)
>
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 4 waves
> **Critical Path**: Task 1 (shaders) → Task 5 (integration test) → Task 7 (Zuko) → Task 9 (timeline) → Task 12 (final integration)

---

## Context

### Original Request
El usuario necesita implementar la escena descrita en `21004082-K/Escena.md` — una secuencia cinematográfica de 7 planos (28 segundos) de la confrontación entre Zuko y Ozai de Avatar: The Last Airbender. La escena debe usar OpenGL y el material del curso (librería grafica/), incluyendo sistema de iluminación, mallas, movimiento de cámara y movimiento de personajes.

### Interview Summary
**Key Discussions**:
- **Modelos**: Buscar modelos 3D externos libres (Sketchfab) con fallback a primitivas articuladas
- **Reproducción**: Automática temporizada (28s, 7 planos secuenciales)
- **Iluminación**: Multiple lights shader (1 PointLight + 2 SpotLights, tonos cálidos Nación del Fuego)
- **Escenario**: Detallado (trono ornamentado, pilares, antorchas, paredes/suelo con texturas)
- **Personajes**: Articulados (grafo jerárquico: torso→brazos→antebrazos, piernas, cabeza)
- **Ejecución**: `uv run python -m 21004082-K`

**Research Findings**:
- `multiple_lights_color.vs` usa `uniform mat4 model` (no `transform`) → debe setear `graph.transform_parameter_name = 'model'`
- `multiple_lights_color.fs` requiere `in vec3 color` (vertex colors) → usar `force_color=np.array([R,G,B,A], dtype=np.uint8)` en `load_and_register_mesh()`
- El shader tiene hardcoded `NR_POINT_LIGHTS=1` y `NR_SPOTLIGHTS=2`
- `Scenegraph.render()` maneja uniforms por instancia y globales; spotLights se setean vía `set_global_attributes`
- Programa.md describe un patrón de personaje articulado con cubos/esferas/cilindros y poses como rotaciones

### Metis Review
**Identified Gaps** (addressed):
- Uniform mismatch shader/scenegraph: Resolved — Task 1 incluye adaptar shader y setear `transform_parameter_name = 'model'`
- Vertex colors missing on OBJ: Resolved — todas las llamadas a `load_and_register_mesh` usan `force_color`
- External models may not be articulable: Resolved — Task 2 incluye fallback a primitivas
- Hard cuts vs smooth transitions: Resolved — cortes duros entre planos, movimiento suave dentro de cada plano
- Facial animation scope: Resolved — excluida, Ozai solo mueve la cabeza
- Module name hyphen: Resolved — el __main__.py ya funciona (no se cambia)
- Timeline drift: Resolved — Task 9 usa tiempo transcurrido real, no frame count

---

## Work Objectives

### Core Objective
Implementar una escena 3D cinematográfica completa en `21004082-K/` que reproduzca automáticamente los 7 planos descritos en Escena.md, con iluminación cálida, personajes articulados y escenario detallado, usando exclusivamente la librería grafica/ del repositorio.

### Concrete Deliverables
- `21004082-K/__init__.py` — aplicación principal completa
- `21004082-K/vertex_program.glsl` — shader de vértices (basado en multiple_lights_color.vs)
- `21004082-K/fragment_program.glsl` — shader de fragmentos (basado en multiple_lights_color.fs)
- `21004082-K/assets/` — modelos 3D descargados o primitivas
- Sistema de luces: 1 PointLight (luz cálida general) + 2 SpotLights (antorcas)
- Personaje Zuko articulado con grafo jerárquico
- Personaje Ozai articulado con grafo jerárquico (simplificado)
- Escenario: trono, 4-6 pilares, suelo, 2 paredes, 2 antorchas
- Timeline de 7 planos con cámara y poses
- Controles: ESPACIO=pausar, R=reiniciar, ESC=salir

### Definition of Done
- [ ] `uv run python -m 21004082-K` abre ventana 3D sin errores
- [ ] La escena reproduce los 7 planos en 28 segundos automáticamente
- [ ] La iluminación proyecta tonos cálidos (naranja/rojo) sobre la escena
- [ ] Zuko tiene articulaciones que rotan en los planos 3, 5, 6
- [ ] El escenario contiene trono, pilares, antorchas y paredes
- [ ] No hay errores de shader ni OpenGL en consola
- [ ] No se modificó la librería grafica/

### Must Have
- Shaders de iluminación multiple_lights (PointLight + SpotLights) adaptados
- Personajes con grafo de escena jerárquico articulado
- 7 planos cinematográficos secuenciales automaticamente
- Iluminación cálida (tonos naranja/rojo Nación del Fuego)
- Escenario con trono, pilares, antorchas, paredes y suelo
- Reproducción automática temporizada de 28 segundos
- Controles de teclado (pausar, reiniciar)

### Must NOT Have (Guardrails)
- NO modificar archivos de la librería grafica/
- NO incluir audio, música ni efectos de sonido
- NO animación facial (boca, expresiones) — Ozai solo rota la cabeza
- NO efectos de partículas (fuego, humo)
- NO detección de colisiones ni física
- NO más de 2 personajes
- NO más de 3 luces (el shader hardcodea NR_POINT_LIGHTS=1, NR_SPOTLIGHTS=2)
- NO techo de la sala del trono
- NO usar `float [0-1]` para force_color — debe ser `uint8 [0-255]`
- NO usar `pyglet.clock.schedule` (variable rate) — debe ser `schedule_interval`

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** - ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO
- **Automated tests**: NO
- **Framework**: none (visual/manual only)
- **Verification**: Agent-Executed QA — ejecutar `uv run python -m 21004082-K` y verificar

### QA Policy
Every task includes agent-executed QA scenarios.
Evidence saved to `.omo/evidence/task-{N}-{scenario-slug}.{ext}`.

- **3D Scene/OpenGL**: Use tmux — run `uv run python -m 21004082-K`, verify window opens, check stderr for errors, capture screenshot
- **Code inspection**: Use grep/read to verify patterns (force_color, transform_parameter_name, schedule_interval)
- **Shader integration**: Run minimal test scene, verify rendering is not black

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation):
├── Task 1: Shaders GLSL (adapt multiple_lights) [quick]
├── Task 2: Find/download 3D models [quick]
├── Task 3: Lighting configuration module [quick]
├── Task 4: Camera system module [quick]
├── Task 5: Integration test scaffold (minimal scene) [unspecified-high]

Wave 2 (After Wave 1 — core construction):
├── Task 6: Throne room environment [unspecified-high] (depends: 1, 2, 3)
├── Task 7: Zuko articulated character [deep] (depends: 1, 2, 3)
├── Task 8: Ozai articulated character [unspecified-high] (depends: 1, 2, 3)
├── Task 9: Timeline & shot director system [deep] (depends: 4)

Wave 3 (After Wave 2 — integration):
├── Task 10: Lighting setup per-shot (torch spots, ambient) [unspecified-high] (depends: 6, 7, 8, 9)
├── Task 11: Character animation poses per-shot [deep] (depends: 7, 8, 9)
├── Task 12: Final __init__.py integration + controls [deep] (depends: 6, 7, 8, 9, 10, 11)

Wave FINAL (After ALL tasks — 4 parallel reviews):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
├── Task F4: Scope fidelity check (deep)
-> Present results -> Get explicit user okay

Critical Path: Task 1 → Task 5 → Task 7 → Task 9 → Task 11 → Task 12 → F1-F4
Parallel Speedup: ~65% faster than sequential
Max Concurrent: 5 (Wave 1)
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1 | - | 5, 6, 7, 8, 10 |
| 2 | - | 5, 6, 7, 8 |
| 3 | - | 5, 6, 7, 8, 10 |
| 4 | - | 5, 9, 12 |
| 5 | 1, 2, 3, 4 | 6, 7, 8, 9 (validates approach) |
| 6 | 1, 2, 3 | 10, 12 |
| 7 | 1, 2, 3 | 10, 11, 12 |
| 8 | 1, 2, 3 | 10, 11, 12 |
| 9 | 4 | 10, 11, 12 |
| 10 | 6, 7, 8, 9 | 12 |
| 11 | 7, 8, 9 | 12 |
| 12 | 6, 7, 8, 9, 10, 11 | F1-F4 |

### Agent Dispatch Summary

- **Wave 1**: 5 tasks — T1 → quick, T2 → quick, T3 → quick, T4 → quick, T5 → unspecified-high
- **Wave 2**: 4 tasks — T6 → unspecified-high, T7 → deep, T8 → unspecified-high, T9 → deep
- **Wave 3**: 3 tasks — T10 → unspecified-high, T11 → deep, T12 → deep
- **FINAL**: 4 tasks — F1 → oracle, F2 → unspecified-high, F3 → unspecified-high, F4 → deep

---

## TODOs

- [x] 1. Shaders GLSL — Adaptar multiple_lights_color a 21004082-K/

  **What to do**:
  - Copiar `assets/multiple_lights_color.vs` → `21004082-K/vertex_program.glsl`
  - Copiar `assets/multiple_lights_color.fs` → `21004082-K/fragment_program.glsl`
  - En el vertex shader, cambiar `uniform mat4 model` → `uniform mat4 transform` (para que coincida con el default de Scenegraph)
  - En el fragment shader, cambiar `uniform vec3 viewPosition` → `uniform vec3 view_position` (snake_case, consistente con el repo)
  - En el fragment shader, cambiar `uniform mat4 model` en vertex → ya cambiada a `transform`
  - Verificar que los structs (Material, PointLight, SpotLight) y funciones (CalcPointLight, CalcSpotLight) se mantienen intactos
  - Verificar que `NR_POINT_LIGHTS=1` y `NR_SPOTLIGHTS=2` se mantienen

  **Must NOT do**:
  - NO modificar los archivos originales en assets/
  - NO cambiar la lógica de iluminación (solo renombrar uniforms)
  - NO añadir features no presentes (shadows, fog, etc.)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Copia y renombrado de shaders, tarea mecánica
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `context7-mcp`: No se necesita documentación externa

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5)
  - **Blocks**: Tasks 5, 6, 7, 8, 10
  - **Blocked By**: None

  **References**:
  - `assets/multiple_lights_color.vs` — Shader de vértices original a copiar. Contiene `in vec3 position, color, normal`, `uniform mat4 model, view, projection`, outputs `fragPosition, fragOriginalColor, fragNormal`
  - `assets/multiple_lights_color.fs` — Shader de fragmentos original. Contiene structs PointLight/SpotLight, Material, funciones CalcPointLight/CalcSpotLight, `uniform vec3 viewPosition`
  - `grafica/scenegraph.py:26` — `self.transform_parameter_name = 'transform'` (linea 26). Esto confirma que el shader debe usar `transform` no `model`
  - `grafica/scenegraph.py:206-208` — Donde se setea el uniform de transformación durante render()
  - `examples/phong_basico/sphere_vertex_program.glsl` — Patrón de shader que usa `uniform mat4 transform` (consistente con Scenegraph)

  **Acceptance Criteria**:
  - [ ] `21004082-K/vertex_program.glsl` existe y contiene `uniform mat4 transform` (no `model`)
  - [ ] `21004082-K/fragment_program.glsl` existe y contiene `uniform vec3 view_position` (no `viewPosition`)
  - [ ] Los structs PointLight y SpotLight están intactos
  - [ ] `NR_POINT_LIGHTS=1` y `NR_SPOTLIGHTS=2` se mantienen

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Shader compila sin errores
    Tool: Bash (python)
    Preconditions: Shaders GLSL creados en 21004082-K/
    Steps:
      1. Ejecutar: uv run python -c "import pyglet; v=pyglet.graphics.shader.Shader(open('21004082-K/vertex_program.glsl').read(),'vertex'); f=pyglet.graphics.shader.Shader(open('21004082-K/fragment_program.glsl').read(),'fragment'); p=pyglet.graphics.shader.ShaderProgram(v,f); print('OK')"
      2. Verificar que la salida contiene "OK" sin excepciones
    Expected Result: "OK" impreso en stdout, sin ShaderException
    Failure Indicators: ShaderException, ImportError, o cualquier traceback
    Evidence: .omo/evidence/task-1-shader-compile.txt

  Scenario: Shader no contiene uniform "model" en vertex
    Tool: Grep
    Preconditions: vertex_program.glsl creado
    Steps:
      1. Buscar "uniform mat4 model" en vertex_program.glsl
      2. Verificar que no hay matches
    Expected Result: 0 matches para "uniform mat4 model"
    Failure Indicators: 1+ matches encontrados
    Evidence: .omo/evidence/task-1-shader-no-model-grep.txt
  ```

  **Commit**: YES (groups with 2, 3, 4, 5)
  - Message: `feat(21004082-K): shaders GLSL de iluminacion multiple lights`
  - Files: `21004082-K/vertex_program.glsl`, `21004082-K/fragment_program.glsl`

- [x] 2. Buscar y descargar modelos 3D libres

  **What to do**:
  - Buscar modelos 3D libres en Sketchfab u otros repositorios para personajes humanos articulables
  - Buscar al menos 2 modelos (uno masculino tipo guerrero para Zuko, uno tipo rey/trono para Ozai)
  - Descargar en formato OBJ (preferido, compatible con trimesh)
  - Si no se encuentran modelos articulables (partes separadas), descargar un modelo de cuerpo completo y usarlo como malla única (sin articulación)
  - Colocar los modelos en `21004082-K/assets/`
  - Alternativamente, si los modelos no se encuentran o son muy pesados, usar las primitivas del repo (`assets/cube.off`, `assets/sphere.off`, `assets/cylinder.off`) para construir personajes articulados siguiendo el patrón de Programa.md
  - Documentar en `21004082-K/assets/README.md` qué modelos se usaron y de dónde se obtuvieron

  **Must NOT do**:
  - NO usar modelos con copyright restrictivo
  - NO usar modelos GLTF con animación esquelética integrada (requiere skinning complejo)
  - NO pasar más de 1 hora buscando modelos — si no se encuentran, usar primitivas

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Búsqueda web + descarga de archivos, tarea simple
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `context7-mcp`: No aplicable

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4, 5)
  - **Blocks**: Tasks 5, 6, 7, 8
  - **Blocked By**: None

  **References**:
  - `assets/sphere.off` — Primitiva esférica disponible en el repo (fallback)
  - `assets/cube.off` — Primitiva cúbica disponible en el repo (fallback)
  - `assets/cylinder.off` — Primitiva cilíndrica disponible en el repo (fallback)
  - `grafica/scenegraph_nodes.py:138-162` — `_node_from_file()` carga OFF/OBJ/STL via trimesh con `force="scene"`, normaliza escala con `scene.scaled(2.0/scene.scale)`
  - `Programa.md:201-305` — Patrón de articulación con primitivas: torso=cube escalado, cabeza=sphere, brazos=cylinder, etc.
  - `grafica/scenegraph_nodes.py:76` — `force_color=np.array([R,G,B,A], dtype=np.uint8)` — valores 0-255 no 0-1

  **Acceptance Criteria**:
  - [ ] Al menos 2 archivos de modelo 3D en `21004082-K/assets/` (OBJ/OFF) o confirmación de uso de primitivas del repo
  - [ ] Si se usan primitivas, documentar en `21004082-K/assets/README.md`
  - [ ] Los modelos pueden cargarse con trimesh.load() sin error

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Modelos cargan con trimesh
    Tool: Bash (python)
    Preconditions: Modelos descargados en 21004082-K/assets/
    Steps:
      1. Ejecutar: uv run python -c "import trimesh; m=trimesh.load('21004082-K/assets/[modelo].obj', force='scene'); print(f'OK: {len(m.geometry)} geometrias')"
      2. Verificar salida contiene "OK"
    Expected Result: "OK: N geometrias" impreso, sin errores
    Failure Indicators: FileNotFoundError, Exception, o crash
    Evidence: .omo/evidence/task-2-model-load.txt

  Scenario: Fallback a primitivas funciona
    Tool: Bash (python)
    Preconditions: Decision de usar primitivas del repo
    Steps:
      1. Ejecutar: uv run python -c "import trimesh; m=trimesh.load('assets/cube.off'); print(f'OK: {len(m.vertices)} vertices')"
      2. Verificar salida contiene "OK"
    Expected Result: "OK: N vertices" impreso
    Failure Indicators: Exception
    Evidence: .omo/evidence/task-2-primitives-fallback.txt
  ```

  **Commit**: YES (groups with 1, 3, 4, 5)
  - Message: `feat(21004082-K): modelos 3D para personajes y escenario`
  - Files: `21004082-K/assets/*`

- [x] 3. Módulo de configuración de iluminación

  **What to do**:
  - Crear `21004082-K/lighting.py` con funciones para configurar las luces del shader multiple_lights
  - Definir constantes para luces cálidas Nación del Fuego:
    - PointLight: color naranja cálido (ej: ambient=[0.2,0.1,0.05], diffuse=[1.0,0.5,0.2], specular=[0.8,0.4,0.1])
    - SpotLight 1 (antorcha izquierda): color rojo-naranja, position cerca del trono
    - SpotLight 2 (antorcha derecha): color rojo-naranja, position cerca del trono
  - Función `setup_lighting(graph)` que setea los uniforms de luces via `graph.set_global_attributes()`
  - Función `update_light_positions(graph, torch_left_pos, torch_right_pos)` para posiciones dinámicas de antorchas
  - Los structs del shader esperan:
    - PointLight: position(3f), constant(1f), linear(1f), quadratic(1f), ambient(3f), diffuse(3f), specular(3f)
    - SpotLight: position(3f), direction(3f), cutOff(1f), outerCutOff(1f), constant(1f), linear(1f), quadratic(1f), ambient(3f), diffuse(3f), specular(3f)
  - Las luces se pasan como arrays numpy float32 al shader via set_global_attributes
  - IMPORTANTE: Los uniforms de array de structs se pasan como un único array plano segÃºn el layout del struct. Consultar `grafica/scenegraph.py:172-186` para el patrón de set_global_attributes que reshapea y pasa los uniforms.

  **Must NOT do**:
  - NO modificar el shader para añadir más luces
  - NO usar valores float [0-1] cuando el shader espera algo distinto
  - NO hardcodear posiciones de antorchas (parametrizar)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Módulo de configuración con constantes y funciones, sin lógica compleja
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4, 5)
  - **Blocks**: Tasks 5, 6, 7, 8, 10
  - **Blocked By**: None

  **References**:
  - `assets/multiple_lights_color.fs:9-41` — Structs PointLight y SpotLight con sus campos exactos
  - `assets/multiple_lights_color.fs:43-52` — Uniforms globales: viewPosition, pointLights[1], spotLights[2], material
  - `grafica/scenegraph.py:172-186` — Patrón para set_global_attributes: reshapea array numpy y pasa al pipeline via `pipeline[attr] = value`
  - `grafica/scenegraph.py:360-361` — `set_global_attributes(**attrs)` que actualiza global_attributes dict
  - `examples/phong_basico/app.py:86-91` — Patrón de set_global_attributes con projection, view_position, light_color, ambient_light

  **Acceptance Criteria**:
  - [ ] `21004082-K/lighting.py` existe
  - [ ] Define PointLight con tonos cálidos (naranja/rojo)
  - [ ] Define 2 SpotLights para antorchas
  - [ ] `setup_lighting(graph)` setea uniforms via set_global_attributes
  - [ ] Los valores de color usan np.float32

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Lighting module importable
    Tool: Bash (python)
    Preconditions: lighting.py creado
    Steps:
      1. Ejecutar: uv run python -c "import sys; sys.path.insert(0,'21004082-K'); import lighting; print('OK')"
      2. Verificar salida "OK"
    Expected Result: "OK" sin ImportError
    Failure Indicators: ImportError, SyntaxError
    Evidence: .omo/evidence/task-3-lighting-import.txt

  Scenario: Light colors are warm (not white)
    Tool: Bash (python)
    Preconditions: lighting.py creado
    Steps:
      1. Ejecutar: uv run python -c "import sys; sys.path.insert(0,'21004082-K'); from lighting import POINT_LIGHT; print(POINT_LIGHT['diffuse'])"
      2. Verificar que diffuse[0] (R) > diffuse[2] (B) (más rojo que azul)
    Expected Result: R > B (ej: [1.0, 0.5, 0.2])
    Failure Indicators: R <= B (color frío/blanco)
    Evidence: .omo/evidence/task-3-warm-colors.txt
  ```

  **Commit**: YES (groups with 1, 2, 4, 5)
  - Message: `feat(21004082-K): modulo de configuracion de iluminacion`
  - Files: `21004082-K/lighting.py`

- [x] 4. Módulo de sistema de cámara

  **What to do**:
  - Crear `21004082-K/camera.py` con el sistema de cámara cinematográfica
  - Definir 7 configuraciones de cámara (una por plano de Escena.md), cada una con:
    - `eye` (posición de cámara), `at` (punto de mira), `up` (vector up), `fov` (campo de visión)
  - Plano 1 (00:00-00:01): Sobre el hombro de Zuko, estática. eye=[-1.5,1.5,2.5], at=[0,1.2,0], up=[0,1,0], fov=45
  - Plano 2 (00:01-00:07): Zoom in lento. eye empieza=[-1.5,1.5,2.5] y termina=[-0.8,1.6,1.5], at=[0,1.5,0], fov pasa de 45 a 55
  - Plano 3 (00:07-00:11): Perspectiva de Ozai mirando a Zuko. eye=[0,2.0,-1], at=[-0.5,1.5,2], up=[0,1,0], fov=50
  - Plano 4 (00:11-00:16): Primer plano Ozai. eye=[0.3,1.8,-1.5], at=[0,1.8,-2.5], up=[0,1,0], fov=35
  - Plano 5 (00:16-00:20): Perfil izquierdo Zuko. eye=[-2.5,1.5,1.0], at=[-0.5,1.5,1.5], up=[0,1,0], fov=40
  - Plano 6 (00:20-00:25): Sobre el hombro, ligero zoom out. eye=[-1.8,1.6,2.8], at=[0,1.2,0], up=[0,1,0], fov pasa de 50 a 45
  - Plano 7 (00:25-00:28): Contrapicado. eye=[-1.0,0.3,1.5], at=[-0.8,1.8,1.0], up=[0,1,0], fov=55
  - Función `get_camera(shot_index, t_local)` que retorna (view_matrix, projection_matrix) para un plano dado
  - Para el plano 2 y 6 (zoom), interpolar linealmente entre inicio y fin según t_local
  - Para cortes duros entre planos, simplemente cambiar la cámara instantáneamente
  - Función `compute_view(eye, at, up)` que retorna `tr.lookAt(eye, at, up)`
  - Función `compute_projection(fov, aspect, near, far)` que retorna `tr.perspective(fov, aspect, near, far)`

  **Must NOT do**:
  - NO usar Bézier entre planos (cortes duros)
  - NO interpolar rotaciones con Euler (usar lookAt directo)
  - NO más de 7 planos

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Definición de datos de cámara y funciones sencillas de interpolación lineal
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 5)
  - **Blocks**: Tasks 5, 9, 12
  - **Blocked By**: None

  **References**:
  - `21004082-K/Escena.md` — Descripción exacta de los 7 planos con timestamps y tipo de cámara
  - `grafica/transformations.py:192-207` — `lookAt(eye, at, up)` función
  - `grafica/transformations.py:163-166` — `perspective(fovy, aspect, near, far)` función
  - `examples/camera_path/__init__.py:458` — Patrón: `tr.lookAt(camera_pos, lookat_pos, np.array([0,1,0]))` + `tr.perspective(45, float(width)/float(height), 0.1, 100)`
  - `examples/scene_graphs/app.py:85-88` — Patrón básico de cámara: view + projection + register_view_transform + set_global_attributes(projection=projection)
  - `examples/phong_basico/app.py:77-83` — view + projection + register_view_transform

  **Acceptance Criteria**:
  - [ ] `21004082-K/camera.py` existe
  - [ ] Define 7 configuraciones de cámara
  - [ ] `get_camera(shot_index, t_local)` retorna view y projection matrices
  - [ ] Plano 2 interpola eye y fov linealmente según t_local
  - [ ] Todas las matrices son np.float32

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Camera module returns valid matrices
    Tool: Bash (python)
    Preconditions: camera.py creado
    Steps:
      1. Ejecutar: uv run python -c "import sys; sys.path.insert(0,'21004082-K'); import numpy as np; from camera import get_camera; v,p = get_camera(0, 0.0, 16/9); print(f'view shape: {v.shape}, proj shape: {p.shape}')"
      2. Verificar que ambos shapes son (4,4)
    Expected Result: "view shape: (4, 4), proj shape: (4, 4)"
    Failure Indicators: Wrong shape, exception, None return
    Evidence: .omo/evidence/task-4-camera-matrices.txt

  Scenario: Camera changes between shots
    Tool: Bash (python)
    Preconditions: camera.py creado
    Steps:
      1. Ejecutar: uv run python -c "import sys; sys.path.insert(0,'21004082-K'); from camera import get_camera; v1,_=get_camera(0,0,1.7); v2,_=get_camera(3,0,1.7); print(f'different: {not np.array_equal(v1,v2)}')"
      2. Verificar que "different: True"
    Expected Result: "different: True" (planos 1 y 4 tienen cámaras distintas)
    Failure Indicators: "different: False" (misma cámara en planos distintos)
    Evidence: .omo/evidence/task-4-camera-different.txt
  ```

  **Commit**: YES (groups with 1, 2, 3, 5)
  - Message: `feat(21004082-K): modulo de sistema de camara cinematografica`
  - Files: `21004082-K/camera.py`

- [x] 5. Integration test scaffold — escena mínima de prueba

  **What to do**:
  - Crear un script de prueba mínimo `21004082-K/test_shader.py` que:
    1. Crea un Scenegraphsimple
    2. Setea `graph.transform_parameter_name = 'transform'` (el shader adaptado ya usa `transform`)
    3. Carga el shader de Task 1 (vertex_program.glsl + fragment_program.glsl)
    4. Carga un cubo (`assets/cube.off`) con `force_color=np.array([200,100,50,255], dtype=np.uint8)` (naranja)
    5. Setea una PointLight y 2 SpotLights via set_global_attributes
    6. Configura cámara básica
    7. Renderiza un frame
  - Esto valida que el pipeline completo funciona antes de construir la escena completa
  - Si hay errores de uniform mismatch, se detectan aquí
  - IMPORTANTE: El shader usa arrays de structs (pointLights, spotLights). Verificar que set_global_attributes puede pasar estos arrays. Si no funciona, usar `pipeline["spotLights[0].position"] = ...` directamente

  **Must NOT do**:
  - NO construir la escena completa aquí (solo validar el pipeline)
  - NO modificar grafica/ para arreglar problemas — arreglar en el código del test o shader

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Requiere debugging de shader integration y potential uniform mismatch, no trivial
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (but depends on Tasks 1, 3, 4 conceptually)
  - **Blocks**: Tasks 6, 7, 8, 9 (valida que el approach funciona)
  - **Blocked By**: Tasks 1, 3, 4 (necesita shaders, lighting y cámara para test)

  **References**:
  - `examples/phong_basico/app.py:39-91` — Patrón completo: crear Scenegraph, load_and_register_mesh, load_pipeline, register_pipeline, add_object, set_global_attributes
  - `grafica/scenegraph.py:32-44` — `load_and_register_pipeline(name, vertex_path, fragment_path)` para cargar shaders
  - `grafica/scenegraph.py:58-59` — `load_and_register_mesh(name, filename, **kwargs)` — kwargs incluye `force_color`
  - `grafica/scenegraph_nodes.py:76-81` — `force_color=np.array([R,G,B,A])` con valores uint8 0-255
  - `assets/multiple_lights_color.fs:9-52` — Estructura de uniforms del shader

  **Acceptance Criteria**:
  - [ ] `21004082-K/test_shader.py` existe
  - [ ] Al ejecutar, abre ventana y muestra un cubo naranja iluminado (no negro, no blanco)
  - [ ] No hay ShaderException en stderr
  - [ ] No hay errores OpenGL en stderr

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Shader integration test renders colored cube
    Tool: interactive_bash (tmux)
    Preconditions: Tasks 1, 3, 4 completados. Shaders y módulos listos.
    Steps:
      1. tmux send-keys: "uv run python 21004082-K/test_shader.py" Enter
      2. Esperar 3 segundos
      3. Capturar screenshot: tmux capture-pane -p
      4. Verificar que no hay "Traceback" o "ShaderException" en output
      5. Verificar que la ventana abrió (no crash inmediato)
    Expected Result: Ventana abierta, cubo visible (no ventana negra o crash)
    Failure Indicators: Traceback, ShaderException, ImportError, ventana negra
    Evidence: .omo/evidence/task-5-shader-test.txt

  Scenario: No OpenGL errors in shader test
    Tool: Bash
    Preconditions: test_shader.py ejecutándose
    Steps:
      1. Ejecutar en modo debug: uv run python 21004082-K/test_shader.py 2>&1 | head -50
      2. Buscar "GL_INVALID", "error", "Error" en stderr
      3. Verificar que no hay matches
    Expected Result: 0 matches de errores OpenGL
    Failure Indicators: 1+ matches de error
    Evidence: .omo/evidence/task-5-no-gl-errors.txt
  ```

  **Commit**: YES (groups with 1, 2, 3, 4)
  - Message: `test(21004082-K): scaffold de prueba de integracion de shaders`
  - Files: `21004082-K/test_shader.py`

- [x] 6. Escenario — Sala del trono de la Nación del Fuego

  **What to do**:
  - Construir el escenario del trono dentro del Scenegraph en `21004082-K/environment.py`
  - Componentes:
    - **Suelo**: Plano grande (puede usar rectangle_2d rotated o cube escalado y achatado) con textura cálida o color rojizo oscuro
    - **Paredes (2)**: Cubos grandes escalados a izquierda y derecha, color rojo oscuro o textura de piedra
    - **Trono**: Estructura ornamentada con múltiples cubos/cilindros:
      - Base: cube escalado (2.0, 0.2, 1.5)
      - Respaldo: cube escalado (2.0, 1.5, 0.2) posicionado detrás
      - Brazos: 2 cubes pequeños a los lados
      - Decoración: 2 cilindros verticales en los extremos del respaldo (estilo antorchas)
    - **Pilares (4-6)**: Cilindros verticales altos a lo largo de la sala, color gris oscuro o rojo
    - **Antorchas (2)**: Cilindros pequeños en la zona del trono; la luz SpotLight se posiciona en su centro
  - Todos los meshes cargados con `force_color` en uint8 [0-255]
  - Cada componente se añade al Scenegraph con `add_transform` + `add_mesh_instance` + `add_edge`
  - Función `build_environment(graph, pipeline_name)` que construye todo el escenario como hijos de un nodo "environment"

  **Must NOT do**:
  - NO construir techo
  - NO usar texturas externas complejas (usar force_color para colores planos)
  - NO más de 6 pilares
  - NO añadir partículas para fuego de antorchas

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Construcción de múltiples meshes con posicionamiento espacial, requiere geometría 3D
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9)
  - **Blocks**: Tasks 10, 12
  - **Blocked By**: Tasks 1, 2, 3 (shaders, modelos, lighting)

  **References**:
  - `21004082-K/Escena.md:5-6` — Descripción del ambiente: "oscuro, iluminado por tonos cálidos (naranjas y rojos), reflejando la tensión de la Nación del Fuego"
  - `21004082-K/Escena.md:36` — "estructura o pilar metálico"
  - `grafica/scenegraph.py:113-137` — `add_object(name, mesh_name, pipeline_name, parent, transform, **attrs)` para añadir objetos al grafo
  - `grafica/scenegraph_premade.py:29-57` — `rectangle_2d(id, parent, texture)` para planos
  - `grafica/scenegraph_nodes.py:138-162` — `_node_from_file` para cargar meshes
  - `Programa.md:207-215` — Patrón de torso con add_transform + add_mesh_instance (ejemplo de construcción jerárquica)
  - `examples/scene_graphs/app.py:51-57` — Patrón: add_transform → add_mesh_instance → add_edge para el sol

  **Acceptance Criteria**:
  - [ ] `21004082-K/environment.py` existe
  - [ ] `build_environment(graph, pipeline_name)` construye: suelo, 2 paredes, trono, 4-6 pilares, 2 antorchas
  - [ ] Todos los meshes usan force_color con valores uint8
  - [ ] El trono está en el centro-fondo de la sala
  - [ ] Los pilares están distribuidos a los lados

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Environment builds without errors
    Tool: Bash (python)
    Preconditions: Tasks 1-5 completados
    Steps:
      1. Ejecutar: uv run python -c "import sys; sys.path.insert(0,'21004082-K'); import numpy as np; from grafica.scenegraph import Scenegraph; from environment import build_environment; g=Scenegraph('root'); g.register_pipeline('p', __import__('grafica').utils.load_pipeline('21004082-K/vertex_program.glsl','21004082-K/fragment_program.glsl')); build_environment(g,'p'); print(f'nodes: {len(g.nodes)}'); print('OK')"
      2. Verificar que nodes > 10 (múltiples componentes)
      3. Verificar "OK" en output
    Expected Result: "nodes: N" con N>10, "OK" impreso
    Failure Indicators: Exception, nodes <10, no "OK"
    Evidence: .omo/evidence/task-6-env-build.txt

  Scenario: Environment has throne and pillars
    Tool: Bash (python)
    Preconditions: environment.py creado
    Steps:
      1. Ejecutar python check buscando nodos con "trono" y "pilar" en sus nombres
      2. Verificar que hay al menos 1 trono y 4 pilares
    Expected Result: 1+ trono, 4+ pilares encontrados
    Failure Indicators: 0 tronos o <4 pilares
    Evidence: .omo/evidence/task-6-env-components.txt
  ```

  **Commit**: YES (groups with 7, 8, 9)
  - Message: `feat(21004082-K): escenario sala del trono de la Nacion del Fuego`
  - Files: `21004082-K/environment.py`

- [x] 7. Personaje Zuko — articulated character

  **What to do**:
  - Construir Zuko como grafo jerárquico en `21004082-K/zuko.py`
  - Articulaciones (siguiendo patrón de Programa.md):
    - torso → cuello → cabeza (con cicatriz: color distinto en un lado)
    - torso → brazo_izq → antebrazo_izq → mano_izq
    - torso → brazo_der → antebrazo_der → mano_der
    - torso → muslo_izq → pantorrilla_izq → pie_izq
    - torso → muslo_der → pantorrilla_der → pie_der
  - Si se encontró modelo 3D externo articulado: cargar partes separadas como meshes individuales
  - Si no (modelo único o primitivas): usar cubos/esferas/cilindros siguiendo el patrón de Programa.md
  - Cada articulación es un `add_transform` node cuyo `transform` se puede modificar para rotar
  - Espadas (2): cilindros escalados delgados, uno en cada mano (cuando se desenvainan)
  - Colores: armadura roja/oscuro (Nación del Fuego), piel, cicatriz (más roja en lado izquierdo de la cara)
  - Función `build_zuko(graph, pipeline_name, parent='root')` que construye el personaje
  - Función `get_zuko_joints()` que retorna lista de nombres de nodos de articulación rotables
  - Función `apply_zuko_pose(graph, pose_dict)` que aplica rotaciones a las articulaciones

  **Must NOT do**:
  - NO animar facial
  - NO más de 14 articulaciones (mantener simple)
  - NO modificar el modelo 3D externo en Blender (usar tal cual)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Construcción de personaje articulado jerárquico con múltiples articulaciones y poses, tarea compleja
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 8, 9)
  - **Blocks**: Tasks 10, 11, 12
  - **Blocked By**: Tasks 1, 2, 3 (shaders, modelos, lighting)

  **References**:
  - `Programa.md:201-330` — Patrón COMPLETO de articulación: torso_transform, cuello, cabeza, brazos, antebrazos, manos, piernas, pies. Usar este como base directa.
  - `Programa.md:255-263` — Brazos: `tr.translate(±0.4, 0.55, 0.0) @ tr.rotationZ(±π/2)`, antebrazos: `tr.translate(0, -brazo_length, 0)`
  - `Programa.md:278-286` — Piernas: muslos `tr.translate(±0.2, -0.6, 0)`, pantorrillas `tr.translate(0, -muslo_length, 0)`
  - `23004082-K/Escena.md:1-42` — Acciones de Zuko por plano: de espaldas con espada (P1), estático (P2), levanta brazo agresivo (P3), baja y levanta mirada (P5), desenvaina segunda espada (P6), gesticulación amplia (P7)
  - `examples/scene_graphs/app.py:51-82` — Patrón de jerarquía con add_transform + add_mesh_instance + add_edge
  - `grafica/scenegraph.py:113-137` — `add_object(name, mesh_name, pipeline_name, parent, transform, **attrs)`
  - `grafica/scenegraph.py:343-358` — `apply_instance_attributes(node_key, **attrs)` para cambiar atributos runtime

  **Acceptance Criteria**:
  - [ ] `21004082-K/zuko.py` existe
  - [ ] `build_zuko()` construye personaje con 10+ articulaciones
  - [ ] `get_zuko_joints()` retorna lista de nodos rotables
  - [ ] `apply_zuko_pose()` aplica rotaciones a las articulaciones
  - [ ] Zuko tiene 2 espadas (cilindros) en las manos
  - [ ] Los colores usan force_color uint8

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Zuko builds with articulations
    Tool: Bash (python)
    Preconditions: Task 7 en progreso, zuko.py creado
    Steps:
      1. Ejecutar: uv run python -c "import sys; sys.path.insert(0,'21004082-K'); from grafica.scenegraph import Scenegraph; from zuko import build_zuko, get_zuko_joints; g=Scenegraph('root'); build_zuko(g,'p'); joints=get_zuko_joints(); print(f'joints: {len(joints)}'); print(joints)"
      2. Verificar que joints tiene 10+ elementos
    Expected Result: "joints: N" con N>=10, lista de nombres de articulaciones
    Failure Indicators: <10 joints, Exception
    Evidence: .omo/evidence/task-7-zuko-joints.txt

  Scenario: Pose changes joint transforms
    Tool: Bash (python)
    Preconditions: zuko.py creado
    Steps:
      1. Construir Zuko en un grafo
      2. Guardar transform original de "brazo_der"
      3. Aplicar pose con rotación en brazo_der
      4. Verificar que transform de brazo_der cambió
    Expected Result: Transform diferente antes/después de apply_zuko_pose
    Failure Indicators: Transform idéntica (pose no aplicada)
    Evidence: .omo/evidence/task-7-pose-change.txt
  ```

  **Commit**: YES (groups with 6, 8, 9)
  - Message: `feat(21004082-K): personaje Zuko articulado`
  - Files: `21004082-K/zuko.py`

- [x] 8. Personaje Ozai — articulated character (simplified)

  **What to do**:
  - Construir Ozai como grafo jerárquico en `21004082-K/ozai.py`
  - Misma estructura articular que Zuko pero más simplificada (Ozai es estático en la mayoría de planos)
  - Articulaciones: torso, cuello, cabeza, brazos (sin movimiento), piernas (sentado)
  - Ozai está SENTADO en el trono: el torso se posiciona en el trono, piernas flexionadas
  - Función `build_ozai(graph, pipeline_name, parent='root')` que construye y posiciona a Ozai sentado en el trono
  - Función `get_ozai_joints()` que retorna lista de nodos rotables (mínimo: cabeza, torso)
  - Función `apply_ozai_pose(graph, pose_dict)` para cambios mínimos (rotación de cabeza)
  - Colores: túnica roja/negra (Señor del Fuego), pelo largo oscuro, barba
  - Ozai se posiciona en el trono (coordinar posición con Task 6)

  **Must NOT do**:
  - NO animar facial
  - NO piernas de pie (Ozai está sentado)
  - NO más articulaciones que Zuko (mínimo movimiento)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Similar a Zuko pero más simple, reutiliza el patrón
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 9)
  - **Blocks**: Tasks 10, 11, 12
  - **Blocked By**: Tasks 1, 2, 3 (shaders, modelos, lighting)

  **References**:
  - `Programa.md:201-330` — Patrón articular base (mismo que Zuko pero simplificado)
  - `21004082-K/Escena.md:23-24` — Ozai: "expresión severa, imperturbable y altanera. Mueve únicamente la boca" → simplificado a rotación de cabeza
  - `21004082-K/Escena.md:29-30` — "rostro estoico de Ozai" en plano 5
  - `grafica/scenegraph.py:113-137` — add_object para construir jerarquía

  **Acceptance Criteria**:
  - [ ] `21004082-K/ozai.py` existe
  - [ ] `build_ozai()` construye personaje sentado con 5+ articulaciones
  - [ ] `get_ozai_joints()` retorna al menos: cabeza, torso
  - [ ] Ozai está posicionado en el trono (no en el origen)
  - [ ] Los colores usan force_color uint8

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Ozai builds and is positioned on throne
    Tool: Bash (python)
    Preconditions: ozai.py creado
    Steps:
      1. Construir Ozai en grafo
      2. Obtener posición global del nodo "ozai_torso"
      3. Verificar que la posición Z indica que está al fondo (no en z=0)
    Expected Result: Ozai posicionado cerca del trono (z negativo o lejos de cámara)
    Failure Indicators: Ozai en origen (0,0,0) o posición incorrecta
    Evidence: .omo/evidence/task-8-ozai-position.txt

  Scenario: Ozai has minimal joints
    Tool: Bash (python)
    Preconditions: ozai.py creado
    Steps:
      1. Ejecutar get_ozai_joints()
      2. Verificar que "cabeza" está en la lista
    Expected Result: "cabeza" en lista de joints
    Failure Indicators: "cabeza" no encontrada
    Evidence: .omo/evidence/task-8-ozai-joints.txt
  ```

  **Commit**: YES (groups with 6, 7, 9)
  - Message: `feat(21004082-K): personaje Ozai articulado sentado en trono`
  - Files: `21004082-K/ozai.py`

- [x] 9. Timeline & shot director system

  **What to do**:
  - Crear `21004082-K/director.py` con el sistema de timeline cinematográfico
  - Definir los 7 planos con timestamps exactos de Escena.md:
    - Shot 1: 0.0 - 1.0s (plano general sobre hombro)
    - Shot 2: 1.0 - 7.0s (zoom in)
    - Shot 3: 7.0 - 11.0s (acción rápida, Zuko apunta)
    - Shot 4: 11.0 - 16.0s (primer plano Ozai)
    - Shot 5: 16.0 - 20.0s (perfil y contraplano)
    - Shot 6: 20.0 - 25.0s (sobre hombro, zoom out)
    - Shot 7: 25.0 - 28.0s (contrapicado)
  - Diccionario `SHOTS` con:
    ```python
    SHOTS = [
        {"index":0, "start":0.0, "end":1.0, "camera":0, "zuko_pose":"espalda_espada", "ozai_pose":"sentado"},
        {"index":1, "start":1.0, "end":7.0, "camera":1, "zuko_pose":"estatico", "ozai_pose":"sentado"},
        {"index":2, "start":7.0, "end":11.0, "camera":2, "zuko_pose":"apunta_espada", "ozai_pose":"sentado"},
        {"index":3, "start":11.0, "end":16.0, "camera":3, "zuko_pose":"fuera_cuadro", "ozai_pose":"sentado"},
        {"index":4, "start":16.0, "end":20.0, "camera":4, "zuko_pose":"perfil_rabia", "ozai_pose":"sentado"},
        {"index":5, "start":20.0, "end":25.0, "camera":5, "zuko_pose":"desenvania_segunda", "ozai_pose":"sentado"},
        {"index":6, "start":25.0, "end":28.0, "camera":6, "zuko_pose":"determinacion", "ozai_pose":"sentado"},
    ]
    ```
  - Función `get_current_shot(t)` → retorna el shot activo y t_local (tiempo dentro del shot)
  - Función `update_scene(graph, t, width, height)` que:
    1. Determina el shot actual
    2. Obtiene cámara via `camera.get_camera(shot_index, t_local, aspect)`
    3. Registra view y projection en el graph
    4. Aplica pose de Zuko via `zuko.apply_zuko_pose(graph, pose_name)`
    5. Aplica pose de Ozai via `ozai.apply_ozai_pose(graph, pose_name)`
    6. Actualiza posiciones de SpotLights (si las antorchas son estáticas, no cambia)
  - Función `update_lighting(graph, t)` que actualiza uniforms de luz según el shot actual (ej:强度 puede variar)
  - Usar tiempo real transcurrido (no frame count) para evitar drift
  - A los 28s, congelar en el último frame

  **Must NOT do**:
  - NO interpolar entre planos (cortes duros)
  - NO usar más de 7 planos
  - NO bucle (congelar al final)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Sistema de timeline con 7 estados, integración de cámara+personajes+luces, lógica no trivial
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 8)
  - **Blocks**: Tasks 10, 11, 12
  - **Blocked By**: Task 4 (camera system)

  **References**:
  - `21004082-K/Escena.md:1-42` — Timestamps y descripciones de los 7 planos (fuente de verdad)
  - `21004082-K/camera.py` (Task 4) — `get_camera(shot_index, t_local, aspect)` retorna view y projection
  - `examples/camera_path/__init__.py:441-476` — Patrón update_camera_path: calcula t, evalúa posiciones, actualiza view, anima objetos
  - `examples/phong_basico/app.py:192-208` — Patrón update_world: `total_time += dt`, actualiza transform de nodos, `graph.calculate_global_transforms()`
  - `examples/scene_graphs/app.py:105-117` — Patrón update: `total_time += dt`, asigna `graph.nodes["earth"]["transform"]`

  **Acceptance Criteria**:
  - [ ] `21004082-K/director.py` existe
  - [ ] Define 7 shots con timestamps correctos
  - [ ] `get_current_shot(t)` retorna el shot correcto para t en [0,28]
  - [ ] `update_scene()` integra cámara, poses y luces
  - [ ] A t=28+, retorna el último shot (congelado)

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Timeline selects correct shot
    Tool: Bash (python)
    Preconditions: director.py creado
    Steps:
      1. Ejecutar: uv run python -c "import sys; sys.path.insert(0,'21004082-K'); from director import get_current_shot; s,tl = get_current_shot(5.0); print(f'shot: {s[\"index\"]}, t_local: {tl:.1f}')"
      2. Verificar que shot index=1 (5.0s está en plano 2: 1-7s)
    Expected Result: "shot: 1, t_local: 4.0" (5.0 - 1.0 = 4.0 dentro del shot)
    Failure Indicators: shot=0, shot=2, o exception
    Evidence: .omo/evidence/task-9-timeline-shot.txt

  Scenario: Timeline freezes at end
    Tool: Bash (python)
    Preconditions: director.py creado
    Steps:
      1. Ejecutar: uv run python -c "import sys; sys.path.insert(0,'21004082-K'); from director import get_current_shot; s,tl = get_current_shot(30.0); print(f'shot: {s[\"index\"]}')"
      2. Verificar que retorna shot index=6 (último)
    Expected Result: "shot: 6" (congelado en último plano)
    Failure Indicators: Index out of bounds, o shot != 6
    Evidence: .omo/evidence/task-9-timeline-freeze.txt
  ```

  **Commit**: YES (groups with 6, 7, 8)
  - Message: `feat(21004082-K): sistema de timeline y director de planos`
  - Files: `21004082-K/director.py`

- [x] 10. Configuración de iluminación por plano

  **What to do**:
  - En `21004082-K/lighting.py` (o archivo nuevo `lighting_shots.py`), definir cómo cambia la iluminación por plano:
  - Configurar PointLight (luz general cálida):
    - Position: arriba-center de la sala, ej: [0, 4, 0]
    - Constant=1.0, Linear=0.09, Quadratic=0.032
    - Ambient=[0.15,0.08,0.03], Diffuse=[0.8,0.4,0.15], Specular=[0.5,0.25,0.1]
  - Configurar SpotLight 1 (antorcha izquierda):
    - Position: [-2, 2, -1] (cerca del trono, izquierda)
    - Direction: hacia el centro [0.5, -0.5, 0.5] normalizado
    - CutOff=cos(15°), OuterCutOff=cos(25°)
    - Color: rojo-naranja intenso
  - Configurar SpotLight 2 (antorcha derecha):
    - Position: [2, 2, -1]
    - Direction: hacia el centro [-0.5, -0.5, 0.5]
    - Mismos parámetros que SpotLight 1
  - Los uniforms de PointLight se pasan como un array numpy flat de 11 floats al shader (position:3 + constant:1 + linear:1 + quadratic:1 + ambient:3 + diffuse:3 + specular:3 = 15, NO 11). Verificar el layout exacto del struct y crear array float64/float32.
  - IMPORTANTE: Consultar `grafica/scenegraph.py:172-186` para el patrón set_global_attributes. El sistema reshapea y pasa el array. Probar primero con un array del tamaño correcto.
  - Si set_global_attributes no funciona con structs de array, usar acceso directo: `pipeline["pointLights[0].position"] = np.array(...)`

  **Must NOT do**:
  - NO modificar el shader para añadir/quitar luces
  - NO más de 1 PointLight + 2 SpotLights

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Configuración de uniforms de shader con arrays de structs, requiere comprensión del layout GLSL
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 11, 12)
  - **Blocks**: Task 12
  - **Blocked By**: Tasks 6, 7, 8, 9 (necesita todos los componentes para testear iluminación)

  **References**:
  - `21004082-K/vertex_program.glsl` (Task 1) — Shader adaptado
  - `21004082-K/fragment_program.glsl` (Task 1) — Shader con structs PointLight/SpotLight
  - `assets/multiple_lights_color.fs:9-41` — Structs exactos con campos y orden
  - `grafica/scenegraph.py:172-186` — set_global_attributes y cómo reshapea arrays numpy
  - `grafica/scenegraph.py:160-188` — render() donde se pasan global_attributes al pipeline
  - `examples/phong_basico/app.py:86-91` — set_global_attributes(projection, view_position, light_color, ambient_light)

  **Acceptance Criteria**:
  - [ ] PointLight configurada con tonos cálidos (R>G>B)
  - [ ] 2 SpotLights configuradas para antorchas
  - [ ] Los uniforms se pasan al shader sin ShaderException
  - [ ] La iluminación resulta visible (no malla negra)

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Lighting renders with warm tones
    Tool: interactive_bash (tmux)
    Preconditions: Tasks 1-9 completados
    Steps:
      1. Ejecutar escena mínima con un cubo y la iluminación configurada
      2. Capturar screenshot después de 2 segundos
      3. Verificar que el cubo tiene tonos naranja/rojo (no negro, no blanco)
    Expected Result: Cubo visible con tonos cálidos (naranja/rojo)
    Failure Indicators: Cubo negro (sin iluminación), blanco (overexposed), o azul (color frío)
    Evidence: .omo/evidence/task-10-warm-lighting.txt

  Scenario: No shader exception from light uniforms
    Tool: Bash
    Preconditions: lighting configurado
    Steps:
      1. Ejecutar uv run python -m 21004082-K 2>&1 | head -20
      2. Buscar "ShaderException" en output
      3. Verificar 0 matches
    Expected Result: 0 matches de ShaderException
    Failure Indicators: 1+ ShaderException encontradas
    Evidence: .omo/evidence/task-10-no-shader-exception.txt
  ```

  **Commit**: YES (groups with 11, 12)
  - Message: `feat(21004082-K): iluminacion por plano con luces calidas`
  - Files: `21004082-K/lighting.py` o `21004082-K/lighting_shots.py`

- [x] 11. Animación de poses de personajes por plano

  **What to do**:
  - En `21004082-K/poses.py`, definir todas las poses de Zuko y Ozai para cada plano:
  - **Zuko poses**:
    - `espalda_espada` (P1): Brazo derecho abajo sosteniendo espada, de espaldas a cámara
    - `estatico` (P2): Postura neutra, brazo con espada abajo
    - `apunta_espada` (P3): Brazo derecho levantado agresivamente apuntando hacia adelante/cámara, torso inclinado adelante
    - `fuera_cuadro` (P4): No visible o recortado (cámara en Ozai)
    - `perfil_rabia` (P5): Perfil izquierdo, cabeza baja luego levanta con rabia, brazo con espada abajo
    - `desenvaina_segunda` (P6): Espada 1 pasa a mano izquierda, mano derecha desenvaina espada 2, postura de combate (piernas separadas, rodillas flexionadas, espadas cruzadas)
    - `determinacion` (P7): Junto a pilar, gesticulación amplia con cabeza y hombros, postura erguida
  - **Ozai poses**:
    - `sentado` (todos los planos): Sentado en trono, postura estoica. Única variación: leve rotación de cabeza en P4.
  - Cada pose se define como diccionario: `{"torso": tr.rotationX(0.1), "brazo_der": tr.rotationZ(np.pi/3), ...}`
  - Las rotaciones se multiplican con la transformación base: `graph.nodes["torso"]["transform"] = torso_base @ pose["torso"]`
  - Plataforma 3: `brazo_der` rota ~π/2 en Z (brazo horizontal apuntando al frente)
  - Usar `tr.rotationA(angle, axis)` para rotaciones que no causen gimbal lock

  **Must NOT do**:
  - NO animar boca o expresiones faciales
  - NO interpolar poses entre planos (cambios instantáneos)
  - NO usar interpolation complicada (cortes duros = cambio inmediato)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: 7 poses complejas para 14+ articulaciones, requiere comprensión cinematográfica y matemática 3D
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 12)
  - **Blocks**: Task 12
  - **Blocked By**: Tasks 7, 8, 9 (necesita personajes y timeline)

  **References**:
  - `21004082-K/Escena.md:1-42` — Descripción exacta de acciones por plano
  - `21004082-K/Escena.md:14-18` — Plano 3: "Zuko levanta agresivamente su brazo derecho y apunta su espada directamente hacia la cámara"
  - `21004082-K/Escena.md:32-36` — Plano 6: "Pasa la primera espada a su mano izquierda, desenvaina una segunda espada con la mano derecha y adopta inmediatamente una postura de combate defensiva"
  - `Programa.md:333-377` — Patrón apply_pose: `graph.nodes["torso"]["transform"] = torso_transform @ transforms.get("torso", tr.identity())`
  - `grafica/transformations.py:62-89` — `rotationA(theta, axis)` para rotación axis-angle evitando gimbal lock
  - `grafica/transformations.py:29-59` — rotationX, rotationY, rotationZ disponibles

  **Acceptance Criteria**:
  - [ ] `21004082-K/poses.py` existe
  - [ ] Define 7 poses de Zuko
  - [ ] Define 1-2 poses de Ozai
  - [ ] Pose `apunta_espada` rota brazo_der significativamente
  - [ ] Pose `desenvaina_segunda` posiciona 2 espadas

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Poses change zuko arm position
    Tool: Bash (python)
    Preconditions: poses.py creado
    Steps:
      1. Construir Zuko en grafo
      2. Aplicar pose "apunta_espada"
      3. Obtener posición global de "zuko_mano_der"
      4. Aplicar pose "estatico"
      5. Obtener posición global de "zuko_mano_der"
      6. Verificar que las posiciones son diferentes (la mano se movió)
    Expected Result: Posiciones de mano_der diferentes entre poses
    Failure Indicators: Misma posición (pose no aplicada)
    Evidence: .omo/evidence/task-11-pose-arm.txt

  Scenario: Second sword appears in desenvaina pose
    Tool: Bash (python)
    Preconditions: poses.py creado
    Steps:
      1. Construir Zuko
      2. Aplicar pose "desenvaina_segunda"
      3. Verificar que existe nodo "zuko_espada_2" con pipeline != None (visible)
    Expected Result: zuko_espada_2 existe y es visible
    Failure Indicators: Nodo no existe o pipeline=None (oculto)
    Evidence: .omo/evidence/task-11-second-sword.txt
  ```

  **Commit**: YES (groups with 10, 12)
  - Message: `feat(21004082-K): poses de animacion de personajes por plano`
  - Files: `21004082-K/poses.py`

- [x] 12. Integración final — __init__.py con loop principal

  **What to do**:
  - Reescribir `21004082-K/__init__.py` completamente como aplicación de escena:
  - Estructura:
    1. Crear ventana Pyglet (default 960x720)
    2. Crear Scenegraph
    3. Setear `graph.transform_parameter_name = 'transform'` (el shader adaptado ya usa transform)
    4. Cargar y registrar pipeline (vertex_program.glsl + fragment_program.glsl)
    5. Cargar meshes (assets externos o primitivas con force_color)
    6. Llamar `build_environment(graph, 'pipeline')`
    7. Llamar `build_zuko(graph, 'pipeline')`
    8. Llamar `build_ozai(graph, 'pipeline')`
    9. Llamar `setup_lighting(graph)` del módulo de iluminación
    10. Setup cámara inicial
    11. Definir estado: `total_time=0.0`, `paused=False`, `t_loop=None`
    12. `on_draw`: clear color buffer (oscuro cálido: 0.08, 0.04, 0.02), enable depth test, render graph
    13. `on_key_press`: ESPACIO → paused, R → total_time=0.0 (reset), ESC → window.close()
    14. `update(dt)`: si not paused: total_time += dt; if total_time > 28.0: total_time = 28.0 (freeze); call director.update_scene(graph, total_time, width, height)
    15. Registrar callback: `pyglet.clock.schedule_interval(update, 1/60.0)`
    16. `pyglet.app.run(1/60.0)`
  - Color de fondo: oscuro cálido (0.08, 0.04, 0.02) — casi negro con tinte rojo
  - El __main__.py ya está correcto (no se modifica)
  - El command click debe llamarse `tarea` para compatibilidad con __main__.py

  **Must NOT do**:
  - NO modificar __main__.py
  - NO modificar grafica/ library
  - NO usar schedule (sin _interval)
  - NO olvidar glEnable(GL_DEPTH_TEST)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Integración de todos los módulos, loop principal, event handlers, coordinación compleja
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (sequential, after Tasks 10, 11)
  - **Blocks**: F1-F4 (Final Verification)
  - **Blocked By**: Tasks 6, 7, 8, 9, 10, 11

  **References**:
  - `21004082-K/__main__.py:1-4` — Llama `from . import tarea; tarea.callback(800, 600)` — NO MODIFICAR
  - `21004082-K/__init__.py:1-26` — Estado actual (hello world). Reescribir completamente.
  - `examples/phong_basico/app.py:155-210` — Patrón on_draw + on_key_press + update_world + schedule_interval
  - `examples/scene_graphs/app.py:91-119` — Patrón on_draw + update + schedule_interval
  - `examples/camera_path/__init__.py:361-477` — Patrón on_draw + on_key_press + update + schedule_interval con camera switching
  - `grafica/scenegraph.py:139-188` — render() con recalculate_transforms, only_pipelines, pipeline_override
  - `grafica/scenegraph.py:50-53` — `register_view_transform(view_transform, name, set_as_current)`

  **Acceptance Criteria**:
  - [ ] `uv run python -m 21004082-K` abre ventana sin errores
  - [ ] La escena muestra contenido 3D (no pantalla negra o gris)
  - [ ] Los 7 planos se suceden automáticamente en 28 segundos
  - [ ] ESPACIO pausa, R reinicia, ESC cierra
  - [ ] profundidad (depth test) está habilitada
  - [ ] No hay ShaderException en stderr
  - [ ] No se modificó grafica/

  **QA Scenarios (MANDATORY)**:
  ```
  Scenario: Full scene runs 28 seconds
    Tool: interactive_bash (tmux)
    Preconditions: ALL tasks completed
    Steps:
      1. tmux send-keys: "uv run python -m 21004082-K" Enter
      2. Esperar 3 segundos
      3. Capturar stdout/stderr
      4. Verificar: no "Traceback", no "ShaderException", no "Error"
      5. Esperar 15 segundos más (total 18s)
      6. Capturar screenshot
      7. Esperar 13 segundos más (total 31s)
      8. Verificar que no hay crash
    Expected Result: Escena corre 28+ segundos sin crashes, 3D visible
    Failure Indicators: Traceback, crash, ventana cerrada antes de 28s
    Evidence: .omo/evidence/task-12-full-scene-run.txt

  Scenario: Keyboard controls work
    Tool: interactive_bash (tmux)
    Preconditions: Scene running
    Steps:
      1. Enviar ESPACIO (pausa)
      2. Esperar 2s
      3. Verificar que la escena está congelada (no avanza)
      4. Enviar ESPACIO (resume)
      5. Enviar R (reset)
      6. Verificar que reinicia desde el plano 1
    Expected Result: Pausa congela, resume continúa, R reinicia
    Failure Indicators: Pausa no congela, R no reinicia
    Evidence: .omo/evidence/task-12-keyboard-controls.txt

  Scenario: No grafica modifications
    Tool: Bash (git)
    Preconditions: All tasks done
    Steps:
      1. Ejecutar: git diff --stat grafica/
      2. Verificar que output está vacío
    Expected Result: Empty output (no files modified in grafica/)
    Failure Indicators: 1+ file listed (grafica modified)
    Evidence: .omo/evidence/task-12-no-grafica-mod.txt

  Scenario: Scene shows different shots
    Tool: interactive_bash (tmux)
    Preconditions: Scene running
    Steps:
      1. Screenshot at t=2s (plano 2, zoom in)
      2. Screenshot at t=9s (plano 3, espada apuntando)
      3. Screenshot at t=13s (plano 4, Ozai)
      4. Screenshot at t=23s (plano 6, desenvainando)
      5. Comparar visualmente que las 4 screenshots muestran encuadres distintos
    Expected Result: 4 screenshots con encuadres разных (cámara cambia entre planos)
    Failure Indicators: Todos screenshots idénticos (cámara no cambia)
    Evidence: .omo/evidence/task-12-different-shots.txt
  ```

  **Commit**: YES
  - Message: `feat(21004082-K): integracion final de escena cinematografica Zuko vs Ozai`
  - Files: `21004082-K/__init__.py`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .omo/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `uv run python -c "import 21004082-K"` to verify import works. Check all GLSL for syntax. Review all changed files for: `as any`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names.
  Output: `Build [PASS/FAIL] | Shaders [PASS/FAIL] | Files [N clean/N issues] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high`
  Run `uv run python -m 21004082-K` in tmux. Wait 3 seconds. Capture screenshot. Wait 10 seconds. Capture screenshot. Wait 10 more seconds. Capture screenshot. Wait 10 more seconds. Capture screenshot. Verify: window opens, 3D content visible, warm lighting, characters present, different shots visible. Check stderr for errors. Save all to `.omo/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep` [MANUAL - agent timeout, verified manually: 13/13 files match spec, no creep]
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1**: `feat(21004082-K): shaders, models, lighting config y camera system base` - shaders/*, assets/*, __init__.py
- **Wave 2**: `feat(21004082-K): escenario, personajes articulados y timeline director` - __init__.py
- **Wave 3**: `feat(21004082-K): iluminacion por plano, animacion y integracion final` - __init__.py
- **Final**: `feat(21004082-K): escena cinematografica Zuko vs Ozai completa` - all files

---

## Success Criteria

### Verification Commands
```bash
uv run python -m 21004082-K  # Expected: 3D window opens, scene plays for 28 seconds
uv run ruff check 21004082-K/  # Expected: no errors (if ruff available)
git diff grafica/  # Expected: empty (no grafica/ modifications)
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] `uv run python -m 21004082-K` runs without errors
- [ ] 7 planos cinematográficos visibles en 28 segundos
- [ ] Iluminación cálida visible (naranja/rojo)
- [ ] Personajes articulados con movimiento
- [ ] Escenario con trono, pilares, antorchas
- [ ] No modified grafica/ files