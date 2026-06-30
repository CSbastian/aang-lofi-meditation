# Técnicas de Modelación Gráfica — Escena Aang Lo-Fi

Este documento cataloga todas las técnicas de computación gráfica implementadas
en el módulo `21004082-K/`, organizadas por categoría. Cada técnica incluye
referencia al archivo fuente y una breve descripción de su aplicación.

---

## 1. Modelado 3D y Carga de Assets

### 1.1 Formato GLTF (GL Transmission Format)
- **Archivo:** `scene_builder.py`, `aang.py`
- **Descripción:** Carga de modelos `.gltf` con geometría, materiales, texturas y jerarquía de joints mediante `GltfModel`. Los assets incluyen el personaje principal (Aang), árboles, arbustos, roca, pasto, y el piso del bosque.

### 1.2 Geometría Procedural
- **Archivo:** `scene_builder.py` (`_make_circle_floor`), `skybox.py` (`generate_sphere_geometry`)
- **Descripción:** Generación de mallas en CPU sin archivos externos:
  - Piso circular como *triangle fan* con normales y UVs paramétricos.
  - Esfera UV para el skydome con resolución configurable (slices × stacks).

### 1.3 Extracción de Materiales GLTF
- **Archivo:** `scene_builder.py` (`_resolve_texture`, `_is_transparent_material`)
- **Descripción:** Lectura de `base_color_factor`, `base_color_texture` y transparencia desde los materiales del modelo GLTF. Fallback a textura blanca 1×1 cuando no hay textura asignada.

---

## 2. Transformaciones y Espacios

### 2.1 Jerarquía de Transformaciones (TRS)
- **Archivo:** `scene_builder.py` (`_placement`), `aang.py`
- **Descripción:** Composición de matrices 4×4: `T(translate) × Rx × Ry × Rz × S(scale)`. Toda la escena usa transformaciones column-major apiladas.

### 2.2 Grafo de Escena (Scene Graph)
- **Archivo:** `aang.py` (función `setup_aang`), usando `grafica.scenegraph.Scenegraph`
- **Descripción:** Estructura arbórea de nodos con transformaciones locales. El cálculo de transformadas globales se hace mediante DFS (`calculate_global_transforms`). Se usa para la jerarquía de 330 joints del esqueleto de Aang.

### 2.3 Matriz de Transformación Normal
- **Archivo:** `shaders/phong_vertex.glsl`, `shaders/skinning_lbs_vertex.glsl`
- **Descripción:** Las normales se transforman con `transpose(inverse(mat3(transform)))` para mantener la ortogonalidad correcta bajo transformaciones no uniformes.

---

## 3. Skinning y Animación de Personajes

### 3.1 Linear Blend Skinning (LBS)
- **Archivo:** `shaders/skinning_lbs_vertex.glsl`, `aang.py`
- **Descripción:** Cada vértice está influenciado por hasta 4 huesos (`joints`) con pesos (`weights`) que suman 1. La matriz de skinning final es la combinación lineal ponderada de las matrices de cada hueso. 330 joints cargados como un array uniform de `mat4[330]`.

### 3.2 Matrix Palette Skinning
- **Archivo:** `aang.py` (`compute_skin_matrices`), `__init__.py`
- **Descripción:** Las matrices de skinning se calculan en CPU como `global_joint_transform × inverse_bind_matrix` y se suben a la GPU como un buffer de `(n_joints × 16)` floats.

### 3.3 Animación Procedural
- **Archivo:** `aang.py` (`apply_breathing_and_wind`, `_compose_anim`)
- **Descripción:** Animación en tiempo real sin keyframes, usando funciones sinusoidales:
  - **Respiración:** Oscilación vertical (+Y local) de las vértebras de la espina (joints 8–12) con amplitud progresiva.
  - **Viento en la capa:** Rotación en X local de los joints de la capa (14–17) con fases desfasadas para simular una onda.
  - **Cabeza:** Inclinación estática hacia abajo para mirada meditativa.

### 3.4 Lotus Pose (Postura Manual)
- **Archivo:** `aang.py` (`apply_lotus_pose`)
- **Descripción:** Rotación explícita de cada articulación (piernas, brazos, manos, dedos, párpados) para adoptar la postura de loto sentado. Implica:
  - Rotación 3-ejes en cadera, rodilla, tobillo.
  - Cierre de manos (*fist*) con curl progresivo por segmento del dedo.
  - Cierre de párpados (*eye closure*) con dirección opuesta para párpado superior e inferior.
  - Descenso de la pelvis para sentar el modelo en el suelo.

---

## 4. Iluminación

### 4.1 Modelo de Iluminación Phong
- **Archivo:** `shaders/phong_fragment.glsl`, `shaders/skinning_phong_fragment.glsl`
- **Descripción:** Iluminación por fragmento con tres componentes:
  - **Ambiental:** `ambient_strength × light_color × albedo`
  - **Difusa (Lambert):** `max(dot(normal, light_dir), 0) × light_color × albedo`
  - **Especular (Phong):** `(dot(reflect_dir, view_dir))^shininess × light_color`
- **Pipeline separado:** Los objetos estáticos y Aang (skinning) usan pipelines distintos pero el mismo modelo de iluminación.

### 4.2 Luz Direccional
- **Archivo:** `scene_builder.py` (`get_lighting_config`), `__init__.py`
- **Descripción:** Una única luz direccional con dirección fija `(0.4, 0.7, 0.5)` y color `(1.0, 0.95, 0.8)` — tono cálido tipo atardecer.

### 4.3 Niebla Lineal (Fog)
- **Archivo:** `shaders/phong_fragment.glsl`, `shaders/skinning_phong_fragment.glsl`
- **Descripción:** Niebla basada en profundidad `smoothstep(near, far, depth)`. Mezcla lineal entre el color Phong y el color de niebla configurable. Oculta los límites del bosque y da profundidad a la escena.

---

## 5. Cámara y Navegación

### 5.1 Cámara Arcball
- **Archivo:** `camera.py` (clase `LoFiCamera`), usando `grafica.arcball.Arcball`
- **Descripción:** Cámara orbital que permite rotar (click izquierdo), panear (click derecho) y hacer zoom (rueda / click medio). La matriz de pose se mantiene como una matriz 4×4 de cámara-a-mundo.

### 5.2 Movimiento WASD con Límites
- **Archivo:** `camera.py`
- **Descripción:** Movimiento del centro de órbita en el plano horizontal usando las teclas WASD. El movimiento se proyecta al plano horizontal (y=0) y se restringe a una caja delimitadora alrededor del target original.

### 5.3 Damping Exponencial
- **Archivo:** `camera.py` (método `update`)
- **Descripción:** Interpolación exponencial (`alpha = 1 - exp(-damping * dt * 60)`) sobre el target y la pose de la cámara para transiciones suaves al soltar el mouse o las teclas.

### 5.4 AABB para Encuadre de Cámara
- **Archivo:** `aang.py` (`compute_aang_bbox`)
- **Descripción:** Cálculo de Axis-Aligned Bounding Box del modelo skineado en CPU. Se usa para posicionar la cámara inicial automáticamente según el tamaño del personaje.

---

## 6. Sistema de Partículas

### 6.1 Estructura Structure-of-Arrays (SoA)
- **Archivo:** `particles3d.py` (clase `ParticleSystem3D`)
- **Descripción:** Arrays paralelos para position, velocity, color, size, age, etc. Cada propiedad es un array NumPy independiente, facilitando operaciones vectorizadas.

### 6.2 Emisión y Ciclo de Vida
- **Archivo:** `particles3d.py` (`emit`, `update`)
- **Descripción:** Las partículas se emiten desde el dosel de los árboles, caen con velocidad vertical negativa y deriva lateral, y se detienen al tocar el suelo (Y=0). Después de un tiempo en el suelo, expiran y se re-emiten automáticamente para mantener densidad constante.

### 6.3 Turbulencia Lateral (Fluttering)
- **Archivo:** `particles3d.py` (`update`)
- **Descripción:** Las hojas en el aire tienen perturbación sinusoidal lateral para simular el planeo y bamboleo de una hoja cayendo.

### 6.4 Point Sprites
- **Archivo:** `shaders/particle_vertex.glsl`, `shaders/particle_fragment.glsl`
- **Descripción:** Las partículas se renderizan como `GL_POINTS` cuyo tamaño se atenúa con la distancia (`point_size_scale * size / gl_Position.w`). El fragment shader genera un círculo suave procedural mediante `gl_PointCoord` con *smoothstep* para el antialiasing del borde.

### 6.5 Atenuación por Profundidad
- **Archivo:** `shaders/particle_fragment.glsl`
- **Descripción:** El alpha de las partículas se atenúa exponencialmente con la distancia (`exp(-depth * 0.01)`) para dar sensación de niebla atmosférica ligera.

---

## 7. Cielo y Ambiente

### 7.1 Skydome Procedimental (Estrellas)
- **Archivo:** `skybox.py`, `shaders/skybox_fragment.glsl`, `shaders/skybox_vertex.glsl`
- **Descripción:** Esfera texturizada proceduralmente:
  - **Estrellas:** Generadas con funciones hash deterministas (`hash21`, `hash22`) que producen una distribución pseudoaleatoria basada en coordenadas esféricas, sin texturas externas.
  - **Tres escalas de estrellas:** Múltiples octavas con diferente densidad y brillo.
  - **Colores espectrales:** Distribución de tipos espectrales (azul, blanco-azul, blanco) para realismo.

### 7.2 Ciclo Día-Noche
- **Archivo:** `shaders/skybox_fragment.glsl`
- **Descripción:** Interpolación entre 4 momentos del día (amanecer, día, atardecer, noche) con transiciones suaves. La visibilidad de estrellas se desvanece durante el día.

### 7.3 Skybox Equirectangular (Zen)
- **Archivo:** `zen_sky.py`, `shaders/zen_skybox_fragment.glsl`, `shaders/zen_skybox_vertex.glsl`
- **Descripción:** Implementación alternativa del cielo que genera texturas 2K equirectangulares en CPU con:
  - **Gradiente vertical** con control de curva (exponente 0.7/0.9) para horizonte amplio.
  - **Montañas lejanas** modeladas como ondas senoidales multioctava.
  - **Luna** dibujada directamente en la textura con difuminado radial.
  - **Crossfade** entre texturas para transiciones suaves día-noche.

### 7.4 Skydome Infinito
- **Archivo:** `skybox.py` (`render_skybox`), `zen_sky.py` (`render_zen_skybox`)
- **Descripción:** La traslación de la matriz de vista se anula (`view[0:3, 3] = 0`) para que el cielo siempre rodee la cámara, dando sensación de infinito.

---

## 8. Renderizado y Pipeline

### 8.1 Múltiples Pipelines GLSL
- **Archivo:** `__init__.py`, `shaders/`
- **Descripción:** Cuatro pipelines de shaders compilados por separado:
  - **Phong:** Objetos estáticos de la escena (árboles, roca, pasto, piso).
  - **Skinning Phong:** Personaje skineado (Aang).
  - **Partículas:** Sistema de puntos con tamaño variable.
  - **Skybox:** Esfera procedural con estrellas.

### 8.2 Vertex Lists Indexados
- **Archivo:** `scene_builder.py` (`_make_vertex_list`), `aang.py`, `skybox.py`
- **Descripción:** Uso de `pipeline.vertex_list_indexed` para enviar geometría a la GPU con índices compartidos (GL_TRIANGLES). Los atributos se copian como arrays planos flatten.

### 8.3 Ordenamiento por Transparencia
- **Archivo:** `__init__.py` (bucle `on_draw`)
- **Descripción:** Las primitivas se separan en opacas y transparentes. Las transparentes se renderizan después, con `glDepthMask(GL_FALSE)` para evitar que bloqueen a otras transparentes.

### 8.4 Alpha Testing (Discard)
- **Archivo:** `shaders/phong_fragment.glsl`, `shaders/skinning_phong_fragment.glsl`
- **Descripción:** Fragmentos con alpha menor a `alpha_cutoff` se descartan con `discard`, evitando artefactos en el depth buffer de texturas con transparencia.

### 8.5 GL_REPEAT para Texturas
- **Archivo:** `scene_builder.py`
- **Descripción:** La textura del piso se configura con `GL_REPEAT` en ambos ejes y los UVs se multiplican por `FLOOR_TILE_REPEAT` para lograr un patrón repetido sin costuras.

---

## 9. Interfaz de Usuario (HUD)

### 9.1 Overlay 2D sobre 3D
- **Archivo:** `__init__.py` (uso de `ui_overlay`), `grafica.ui`
- **Descripción:** Renderizado de elementos 2D (texto, sprites) sobre la escena 3D mediante una proyección ortográfica que desactiva el depth buffer.

### 9.2 Pomodoro Timer
- **Archivo:** `pomodoro.py` (clase `Pomodoro`)
- **Descripción:** Timer visual con:
  - **Carga de textura** desde archivo WEBP con redimensión PIL.
  - **Sprite circular** del loto blanco como fondo.
  - **Barra de progreso circular** usando `pyglet.shapes.Arc`.
  - **Labels** con fuente Fira Code para estado, tiempo y modo.
  - **Ciclo** trabajo 25 min / descanso 5 min con colores diferenciados (cálido/frío).

---

## 10. Audio

### 10.1 Carga y Reproducción de Audio (Deshabilitado)
- **Archivo:** `audio.py` (`load_lofi_audio`, `toggle_audio`, `set_audio_volume`)
- **Descripción:** Carga de archivos de audio MP3 con `pyglet.media.load`, loop infinito, y control de reproducción. Actualmente deshabilitado en la escena pero el código está presente.

---

## 11. Interacción y Eventos

### 11.1 Entrada de Teclado
- **Archivo:** `__init__.py` (`on_key_press`), `camera.py` (`on_key_press_WASD`)
- **Descripción:** Múltiples modos de interacción:
  - `WASD`: Movimiento de cámara.
  - `R`: Reset de cámara.
  - `SPACE`: Pausa/reanuda tiempo de la escena.
  - `M`: Activa/desactiva audio.
  - `P`: Pausa/reanuda Pomodoro.
  - `N`: Salta al siguiente período Pomodoro.
  - `ESCAPE`: Cierra la ventana.

### 11.2 Entrada de Mouse
- **Archivo:** `camera.py` (`on_mouse_press`, `on_mouse_drag`, `on_mouse_scroll`)
- **Descripción:** Click izquierdo orbita, derecho pan, rueda zoom. El estado del Arcball se selecciona según el botón presionado.

---

## 12. Gestión de Memoria GPU

### 12.1 Subida de Texturas
- **Archivo:** `scene_builder.py` (vía `model.upload_textures()`), `__init__.py`
- **Descripción:** Las texturas se suben a la GPU inmediatamente después de crear el contexto OpenGL. Los modelos GLTF se descargan de RAM (`del model`) después de extraer los vertex lists y textures IDs, manteniendo solo los datos en GPU.

### 12.2 Buffer de Skinning en GPU
- **Archivo:** `__init__.py` (líneas 138-140)
- **Descripción:** Buffer de matrices de skinning como `(GLfloat * 16) * n_joints` que se actualiza cada frame desde un view de NumPy sin allocaciones.

---

## Resumen de Técnicas por Archivo

| Archivo | Técnicas Principales |
|---|---|
| `__init__.py` | Orquestación de pipelines, renderizado multishader, ordenamiento por transparencia, eventos |
| `scene_builder.py` | Carga GLTF, geometría procedural, composición TRS, scattering, texturas REPEAT |
| `aang.py` | LBS, scene graph, animación procedural, lotus pose, AABB, skin matrices |
| `camera.py` | Arcball, damping exponencial, WASD, límites de movimiento |
| `particles3d.py` | Sistema SoA, turbulencia, colisión suelo, ciclo de vida |
| `skybox.py` | Esfera UV, estrellas procedurales, ciclo día-noche |
| `zen_sky.py` | Textura equirectangular procedural, crossfade, montañas, luna |
| `pomodoro.py` | UI overlay, sprites, arco de progreso, timer |
| `audio.py` | Carga MP3, loop, control volumen |
| `shaders/phong_*.glsl` | Phong lighting, niebla lineal, alpha discard, normal matrix |
| `shaders/skinning_*.glsl` | LBS, palette skinning, Phong + niebla |
| `shaders/skybox_*.glsl` | Skydome, hash estrellas, ciclo día-noche |
| `shaders/particle_*.glsl` | Point sprites, atenuación distancia, círculo procedural |
