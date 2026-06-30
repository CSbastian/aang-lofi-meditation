# Draft: Escena 3D de Aang Meditando (Lo-Fi)

## Requirements (confirmed)
- Implementar escena descrita en `21004082-K/Escena.md` dentro del paquete `21004082-K/`
- Escena 3D de Aang meditando con música Lo-Fi
- Cámara interactiva: teclado (WASD) para desplazamiento lateral/avance/retroceso con límites; ratón para orbitar alrededor de Aang con suavizado (damping)
- Fondo: árboles, arbustos y hongos
- Assets glTF disponibles en `21004082-K/assets/`

## Entregable (convención del curso)
- Punto de entrada: `21004082-K/__init__.py` define comando click `tarea(width, height)` → `__main__.py` llama `tarea.callback(800,600)`
- Actualmente `tarea` muestra "¡Hola, CC3501!" → REEMPLAZAR por la escena 3D completa
- Se ejecuta via: `uv run python caja_de_juguetes.py tarea` (TBC por explore agent)

## Assets glTF disponibles (todos: scene.gltf + scene.bin + textures/)
- `amanita_muscaria_mushroom/` — hongo amanita (rojo con puntos blancos)
- `avatar_aang_fortnite/` — modelo de Aang (1.6MB, el personaje principal)
- `cliff_shrub_for_terrain/` — arbusto para terreno
- `grass_claster__downoad__like_please/` — cluster de pasto
- `realistic_trees_pack_of_2_free/` — pack de 2 árboles realistas (64MB! pesado)
- `tree grande/` — árbol grande (el árbol gigante en primer plano)

## Elementos de la escena (según Escena.md)
1. **Aang** — postura de loto (Padmasana), espalda recta, manos en Dhyana Mudra, ojos cerrados, ligera inclinación cabeza abajo. Centro del encuadre inferior.
2. **Árbol gigante** — primer plano a la derecha, actúa como marco. Hongos nacen de la corteza apuntando al centro.
3. **Muro de roca púrpura** — medio plano, justo detrás del personaje, horizontal, separa meditación del bosque.
4. **Árboles de fondo** — múltiples capas (cerca/lejos) para parallax. Vegetación densa detrás del muro.
5. **Viento en ropa** — cloth physics en túnica de Aang (ondulaciones lentas)
6. **Viento en entorno** — shader de viento en hojas de arbustos y musgo (balanceo armónico)
7. **Respiración de Aang** — animación idle cíclica: pecho/hombros se inflan/desinflan lentamente
8. **Partículas mágicas** — puntos de luz amarilla/verde pálida (esporas/luciérnagas) flotando de abajo hacia arriba, patrones caóticos suaves
9. **Cámara orbital** — WASD desplazamiento con límites; ratón rotación con damping
10. **Niebla volumétrica** — color verde amarillento en fondo, atmósfera mística
11. **Profundidad de campo** — Aang enfocado, árboles lejanos desenfocados
12. **Audio Lo-Fi** — fuente de audio con loop, pista chillhop/lo-fi (2D o 3D)

## User Decisions (entrevista)
- **Audio**: "Yo proveo el archivo" → el plan asume que el usuario colocará un track Lo-Fi en assets/. Hacer la ruta configurable.
- **Fidelidad**: "particulas flotando, y un sistema de iluminacion de phong" → aproximaciones educacionales con énfasis en:
  - Sistema de iluminación Phong (escribir shaders custom)
  - Partículas flotando (3D, esporas/luciérnagas)
  - El resto (cloth, DoF, niebla volumétrica) como aproximaciones simples o simplificado

## Technical Decisions
- **Iluminación**: Phong custom (vertex + fragment shader) — NO existe en grafica/, escribir desde cero. Referencia: examples/phong_basico/ y examples/sistema_tierra/
- **Partículas**: ParticleSystem de grafica/ es 2D solo → extender a 3D o construir sistema custom. Puntos de luz amarilla/verde pálida flotando hacia arriba.
- **Cámara**: Arcball (grafica/arcball.py) para orbitar con ratón + WASD custom para desplazamiento con límites + damping
- **Niebla**: Aproximación shader de distancia (no volumétrica real) — implementar en fragment shader del Phong
- **Audio**: pyglet.media (no wrapper en grafica/) — cargar track, loop=True
- **GLTF**: grafica/gltf.py soporta carga + skinning + animaciones. Referencia: examples/skinning/
- **Scene graph**: Scenegraph (grafica/scenegraph.py) — registrar pipelines, meshes, construir jerarquía

## Research Findings
### Capability map de grafica/ (bg_281e70c6)
**SÍ soportado**: Scene graph (networkx), transformations (lookAt, perspective, etc.), GLTF loader (gltf.py — con skinning y animaciones!), Arcball camera, textures, background gradient, framebuffers (depth-only), particle system (¡2D solo!)
**NO soportado (construir desde cero)**: Lighting shaders (Phong — no hay en lib, solo en examples/), fog, DoF, audio, 3D particles
**Referencias clave en examples/**:
- examples/skinning/ — GLTF + skinning + Arcball + I/O completo (MEJOR referencia)
- examples/arcball/ — patrón de cámara orbital
- examples/sistema_tierra/ — scene graph complejo + iluminación + texturas

### Patrones de examples/ (bg_c9f38af3)
- **Convención del entregable**: `21004082-K/__init__.py` define `@click.command("tarea")` con `--width`/`--height` → crea Window, setup Scenegraph, Arcball, event handlers, pyglet.app.run()
- **View matrix por frame**: `current_view = np.linalg.inv(arcball.pose)` → `graph.views[graph.current_view] = current_view`
- **Import pattern**: `import grafica.transformations as tr`, `from grafica.arcball import Arcball`, `from grafica.scenegraph import Scenegraph`, etc.
- **Shaders**: cargar con `load_pipeline(vertex_path, fragment_path)` → `graph.register_pipeline(name, pipeline)`
- **Update loop**: `pyglet.clock.schedule_interval(update, 1/60.0)` para animación

### Análisis de referencia.png
- **FALLO**: No se pudo analizar la imagen (timeout reiterado). Se procede con la descripción detallada de Escena.md.

### Modelo de Aang (inspección glTF directa)
- 339 nodos, 2 meshes, 1 skin, 0 animaciones
- Esqueleto rigged completo: pelvis → spine (5 vértebras) → neck → head; brazos, piernas, **capa (cape) con joints propios**
- **Pose estática de pie (T/A-pose de Fortnite), NO postura de loto**
- Sin animaciones incluidas → respiración y viento en capa requieren animar joints manualmente vía skinning

## Open Questions
- ¿El modelo de Aang glTF ya viene en postura de loto o hay que posarlo? (probablemente viene en pose T de Fortnite — requiere análisis)
- ¿Hay un archivo de audio Lo-Fi provisto o hay que conseguirlo?
- ¿Cloth physics realista es factible en Pyglet/PyOpenGL o se simula con shader/vertex animation?
- ¿Qué tan fiel debe ser la implementación de cada elemento (ej: ¿DoF real o aproximado)?
- ¿Prioridad: todos los elementos o hay un subconjunto mínimo aprobable?

## Scope Boundaries
- INCLUDE: (TBC)
- EXCLUDE: (TBC)
