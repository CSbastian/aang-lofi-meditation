# Explicación del Programa: Modelo Articulado 3D

Este documento describe detalladamente la implementación de la tarea ubicada en el directorio `21004082-K/`. El programa consiste en un visualizador interactivo de un personaje articulado en 3D (estilo muñeco) utilizando **Pyglet**, **PyOpenGL** y un grafo de escena jerárquico. El usuario puede alternar entre distintas poses del personaje presionando la barra espaciadora.

El proyecto se compone de tres archivos principales:

1. `__init__.py`: Contiene toda la lógica de la aplicación, la construcción del grafo de escena, las poses y el ciclo de renderizado.
2. `vertex_program.glsl`: Shader de vértices encargado de transformar la geometría y preparar los datos para el fragment shader.
3. `fragment_program.glsl`: Shader de fragmentos encargado del sombreado, aplicando iluminación ambiental y difusa.

---

## 1. `vertex_program.glsl` — Shader de Vértices

Este shader se ejecuta una vez por cada vértice de la malla. Su trabajo es transformar las coordenadas locales del modelo a la pantalla y preparar variables para el shader de fragmentos.

### Version y Entradas

```glsl
#version 330
in vec3 position;
in vec3 normal;
```

- `#version 330`: Especifica que se usa OpenGL 3.3 (core profile).
- `in vec3 position`: Coordenadas locales (x, y, z) del vértice, provenientes del buffer de geometría.
- `in vec3 normal`: Vector normal del vértice, usado para cálculos de iluminación.

### Uniforms

```glsl
uniform vec3 color;
uniform mat4 transform;
uniform mat4 view;
uniform mat4 projection;
```

- `color`: Color base del objeto, pasado como uniform desde Python.
- `transform`: Matriz de transformación del modelo (model matrix), que incluye traslación, rotación y escala del nodo en el grafo de escena.
- `view`: Matriz de vista (view matrix), que posiciona la cámara en el mundo.
- `projection`: Matriz de proyección en perspectiva, que define el frustum y la perspectiva 3D.

### Salidas al Fragment Shader

```glsl
out vec3 fragColor;
out vec3 fragNormal;
out vec3 fragPosition;
```

- `fragColor`: Se interpola entre vértices y se envía al fragment shader.
- `fragNormal`: Normal transformada al espacio del mundo.
- `fragPosition`: Posición del vértice en coordenadas del mundo.

### Función Principal

```glsl
void main()
{
    fragColor = color;
    vec4 worldPos = transform * vec4(position, 1.0);
    fragPosition = worldPos.xyz;
    fragNormal = mat3(transform) * normal;
    gl_Position = projection * view * worldPos;
}
```

1. **Paso de color**: `fragColor = color;` simplemente reenvía el color recibido.
2. **Transformación al espacio mundo**: `worldPos = transform * vec4(position, 1.0)` convierte la posición local a coordenadas mundiales usando la matriz de modelo.
3. **Posición en mundo**: `fragPosition = worldPos.xyz` extrae las coordenadas xyz para interpolarlas.
4. **Transformación de la normal**: `fragNormal = mat3(transform) * normal` rotea la normal usando solo la parte rotacional de la matriz de transformación (notar que se descarta la traslación usando `mat3`). Esto es crucial para que la iluminación sea correcta cuando el objeto rota.
5. **Posición final en pantalla**: `gl_Position = projection * view * worldPos` aplica la cámara y la proyección en perspectiva para obtener las coordenadas normalizadas del dispositivo (NDC). El orden es estándar: primero modelo, luego vista, luego proyección.

---

## 2. `fragment_program.glsl` — Shader de Fragmentos

Este shader se ejecuta una vez por cada píxel cubierto por la geometría. Recibe los valores interpolados desde los vértices y calcula el color final del píxel aplicando un modelo de iluminación simple.

### Entradas y Salida

```glsl
in vec3 fragColor;
in vec3 fragNormal;
in vec3 fragPosition;
out vec4 outColor;
```

- `fragColor`, `fragNormal`, `fragPosition`: Valores interpolados desde el vertex shader para el píxel actual.
- `outColor`: Color final RGBA que se escribe en el framebuffer.

### Función Principal

```glsl
void main()
{
    float ambientStrength = 0.4;
    vec3 ambient = ambientStrength * fragColor;

    vec3 norm = normalize(fragNormal);
    vec3 lightDir = normalize(vec3(1.0, 1.0, 0.5));
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diff * fragColor;

    vec3 result = ambient + diffuse;
    outColor = vec4(result, 1.0);
}
```

1. **Luz Ambiental**: 
   - `ambientStrength = 0.4`: Intensidad de la luz ambiental.
   - `ambient = 0.4 * fragColor`: Multiplica el color base por 0.4. Esto garantiza que las zonas no iluminadas directamente no se vean completamente negras, dando profundidad a la escena.

2. **Luz Difusa**:
   - `norm = normalize(fragNormal)`: Normaliza la normal interpolada para asegurar que tenga longitud 1.
   - `lightDir = normalize(vec3(1.0, 1.0, 0.5))`: Define una fuente de luz direccional que viene desde arriba (y positivo), a la derecha (x positivo) y ligeramente al frente (z positivo).
   - `diff = max(dot(norm, lightDir), 0.0)`: Calcula el coseno del ángulo entre la normal y la dirección de la luz. Si el ángulo es mayor a 90°, el resultado es 0 (la cara está de espaldas a la luz).
   - `diffuse = diff * fragColor`: Escala el color base según la intensidad de la luz difusa.

3. **Mezcla Final**:
   - `result = ambient + diffuse`: Suma ambas contribuciones de luz.
   - `outColor = vec4(result, 1.0)`: Asigna el color final con opacidad total (alfa = 1.0).

Este modelo de iluminación es conocido como **Lambertiano simplificado** con un término ambiental constante.

---

## 3. `__init__.py` — Lógica Principal de la Aplicación

Este archivo contiene toda la lógica de la aplicación: inicialización de la ventana, construcción del grafo de escena jerárquico, definición de poses, manejo de controles y renderizado.

### 3.1. Imports

```python
import os
from pathlib import Path

import numpy as np
import pyglet
from OpenGL import GL
import click

import grafica.transformations as tr
from grafica.utils import load_pipeline
import grafica.scenegraph as SceneGraph
```

- `os` y `Path`: Manejo de rutas de archivos de forma portable.
- `numpy as np`: Operaciones numéricas y manejo de matrices 4x4.
- `pyglet`: Framework para crear ventanas, manejar eventos y ejecutar el loop principal.
- `OpenGL.GL`: Acceso directo a funciones de OpenGL (limpia de buffers, depth test, etc.).
- `click`: Librería para crear interfaces de línea de comandos (CLI) de forma sencilla.
- `grafica.transformations as tr`: Módulo local con funciones de transformación (traslación, rotación, escala, lookAt, perspectiva, etc.).
- `grafica.utils.load_pipeline`: Función para cargar y compilar los shaders GLSL desde archivos.
- `grafica.scenegraph as SceneGraph`: Implementación del grafo de escena basado en NetworkX.

### 3.2. Carga del Pipeline de Shaders

```python
pipeline = load_pipeline(
    Path(os.path.dirname(__file__)) / "vertex_program.glsl",
    Path(os.path.dirname(__file__)) / "fragment_program.glsl",
)
```

- `os.path.dirname(__file__)`: Obtiene el directorio donde se encuentra `__init__.py`.
- `load_pipeline(...)`: Lee ambos archivos `.glsl`, los compila y los enlaza en un programa de shaders de Pyglet (`ShaderProgram`). Este objeto `pipeline` se usará más adelante para dibujar todas las mallas.

### 3.3. Definición del Comando CLI

```python
@click.command("tarea", short_help='¡Hola, mundo!')
@click.option("--width", type=int, default=800)
@click.option("--height", type=int, default=600)
def tarea(width, height):
    win = pyglet.window.Window(width, height)
```

- `@click.command`: Define un comando CLI llamado `tarea`.
- `@click.option`: Permite configurar el ancho y alto de la ventana al ejecutar desde terminal (ej. `uv run python -m 21004082-K --width 1024 --height 768`).
- `pyglet.window.Window(width, height)`: Crea la ventana de renderizado con las dimensiones especificadas.

### 3.4. Creación del Grafo de Escena

```python
graph = SceneGraph.Scenegraph("root")
assets_dir = Path(os.path.dirname(__file__)) / "assets"

graph.load_and_register_mesh("cube", str(assets_dir / "cube.off"), fix_normals=True)
graph.load_and_register_mesh("sphere", str(assets_dir / "sphere.off"), fix_normals=True)
graph.load_and_register_mesh("cylinder", str(assets_dir / "cylinder.off"), fix_normals=True)
graph.register_pipeline("pipeline", pipeline)
```

- `SceneGraph.Scenegraph("root")`: Instancia un grafo de escena con un nodo raíz llamado `"root"`. En este grafo, cada nodo puede tener una transformación local y un mesh asociado.
- `assets_dir`: Ruta a la carpeta `assets/` donde se encuentran los modelos 3D.
- `load_and_register_mesh(...)`: Carga archivos de geometría en formato `.off` y los registra con un nombre clave (`cube`, `sphere`, `cylinder`). `fix_normals=True` asegura que las normales de los vértices estén correctamente calculadas.
- `register_pipeline(...)`: Asocia el programa de shaders cargado previamente bajo el nombre `"pipeline"`.

### 3.5. Construcción del Cuerpo Base

A continuación se definen las transformaciones base de cada parte del cuerpo. Estas transformaciones posicionan y escalan cada articulación en su **posición de reposo** (T-pose o pose neutra). Más adelante se les aplicarán rotaciones adicionales para crear las poses.

#### Torso

```python
torso_transform = tr.identity()
torso_visual = tr.scale(0.8, 1.2, 0.5)
graph.add_transform("torso", torso_transform)
graph.add_transform("torso_visual", torso_visual)

graph.add_mesh_instance("torso_mesh", "cube", "pipeline", color=np.array((0.22, 0.27, 0.45), dtype=np.float32))
```

- `torso_transform = tr.identity()`: El torso está en el origen local.
- `torso_visual = tr.scale(0.8, 1.2, 0.5)`: Escala un cubo para darle forma de torso (más alto que ancho, y delgado en profundidad).
- `add_mesh_instance`: Crea una instancia de la malla `"cube"` usando el pipeline `"pipeline"` y le asigna un color azul oscuro (RGB: 0.22, 0.27, 0.45).

#### Cuello

```python
neck_height = 0.2
cuello_transform = tr.translate(0.0, 0.6, 0.0)
cuello_visual = tr.matmul([tr.translate(0.0, neck_height / 2, 0.0), tr.scale(0.25, neck_height, 0.25)])
graph.add_transform("cuello", cuello_transform)
graph.add_transform("cuello_visual", cuello_visual)
graph.add_mesh_instance("cuello_mesh", "cube", "pipeline", color=np.array((0.92, 0.90, 0.75), dtype=np.float32))
```

- `cuello_transform`: Traslada el origen del cuello hacia arriba desde el torso (y = 0.6).
- `cuello_visual`: Mueve la geometría media unidad hacia arriba (para que pivote desde abajo) y la escala a forma de cuello delgado.
- Color: Beige claro, simulando piel.

#### Cabeza

```python
cabeza_transform = tr.translate(0.0, neck_height + 0.31, 0.0)
cabeza_visual = tr.scale(0.45, 0.62, 0.52)
graph.add_transform("cabeza", cabeza_transform)
graph.add_transform("cabeza_visual", cabeza_visual)
graph.add_mesh_instance("cabeza_mesh", "sphere", "pipeline", color=np.array((0.88, 0.72, 0.58), dtype=np.float32))
```

- `cabeza_transform`: Se posiciona sobre el cuello (`neck_height` más un offset adicional de 0.31).
- `cabeza_visual`: Escala una esfera para darle forma de cabeza ovalada.
- Color: Tono de piel.

#### Brazos y Antebrazos

```python
brazo_length = 0.7
antebrazo_length = 0.7

brazo_izquierdo_transform = tr.matmul([tr.translate(-0.4, 0.55, 0.0), tr.rotationZ(- np.pi / 2)])
brazo_derecho_transform = tr.matmul([tr.translate(0.4, 0.55, 0.0), tr.rotationZ(np.pi / 2)])
antebrazo_izquierdo_transform = tr.translate(0.0, -brazo_length, 0.0)
antebrazo_derecho_transform = tr.translate(0.0, -brazo_length, 0.0)
```

- `brazo_izquierdo_transform`: Se traslada al hombro izquierdo (-0.4 en X) y se rota -90° en Z para que apunte hacia abajo en el eje Y local.
- `brazo_derecho_transform`: Simétrico al izquierdo, pero en el hombro derecho (+0.4 en X) y rotación +90° en Z.
- `antebrazo_izquierdo/derecho_transform`: Se colocan al final del brazo (desplazamiento negativo en Y local de `brazo_length`).

```python
brazo_visual = tr.matmul([tr.translate(0.0, -brazo_length / 2, 0.0), tr.scale(0.2, brazo_length, 0.2)])
antebrazo_visual = tr.matmul([tr.translate(0.0, -antebrazo_length / 2, 0.0), tr.scale(0.18, antebrazo_length, 0.18)])
```

- `brazo_visual`: Mueve la geometría para que su centro esté a la mitad del brazo y la escala a forma de cilindro largo.
- `antebrazo_visual`: Similar, pero ligeramente más delgado (0.18 vs 0.2).

Los colores son azul oscuro para la camisa y piel para los antebrazos.

#### Piernas (Muslo y Pantorrilla)

```python
muslo_length = 0.85
pantorrilla_length = 0.8
muslo_izquierdo_transform = tr.translate(-0.2, -0.6, 0.0)
muslo_derecho_transform = tr.translate(0.2, -0.6, 0.0)
pantorrilla_izquierda_transform = tr.translate(0.0, -muslo_length, 0.0)
pantorrilla_derecha_transform = tr.translate(0.0, -muslo_length, 0.0)
```

- Los muslos salen desde la parte baja del torso (y = -0.6).
- Las pantorrillas están al final de los muslos.

Las mallas son cilindros escalados, con colores azul oscuro.

#### Manos

```python
mano_izquierda_transform = tr.translate(0.0, -antebrazo_length, 0.0)
mano_visual = tr.matmul([tr.translate(0.0, -0.125, 0.0), tr.scale(0.2, 0.15, 0.2)])
```

- Se ubican al final de los antebrazos.
- Son cubos pequeños y achatados, color piel.

#### Pies

```python
pie_visual = tr.matmul([tr.translate(0.0, -0.125, 0.15), tr.scale(0.3, 0.25, 0.6)])
```

- Cubos escalados que simulan zapatos.
- Color gris oscuro (RGB: 0.15, 0.15, 0.18).

### 3.6. Jerarquía de Nodos

```python
graph.add_edge("root", "torso")
graph.add_edge("torso", "torso_visual")
graph.add_edge("torso_visual", "torso_mesh")
graph.add_edge("torso", "cuello")
graph.add_edge("cuello", "cuello_visual")
...
```

- `add_edge("padre", "hijo")`: Conecta los nodos del grafo de escena. Esto define la jerarquía padre-hijo.
- La transformación global de un nodo hijo se calcula como: `transform_global(padre) × transform_local(hijo)`.
- **Estructura jerárquica**:
  - `root` → `torso`
    - `torso` → `torso_visual` → `torso_mesh`
    - `torso` → `cuello` → `cabeza`
    - `torso` → `brazo_izquierdo` → `antebrazo_izquierdo` → `mano_izquierda`
    - `torso` → `brazo_derecho` → `antebrazo_derecho` → `mano_derecha`
    - `torso` → `muslo_izquierdo` → `pantorrilla_izquierda` → `pie_izquierdo`
    - `torso` → `muslo_derecho` → `pantorrilla_derecha` → `pie_derecho`

Esta jerarquía permite que, por ejemplo, al rotar el torso, toda la parte superior e inferior del cuerpo se muevan junto con él.

### 3.7. Definición de las Poses

```python
poses = [
    {"name": "Spike_casual", "camera": {...}, "transforms": {...}},
    {"name": "Spike_pelea", "camera": {...}, "transforms": {...}},
    {"name": "Gymbro", "camera": {...}, "transforms": {...}},
]
```

Se definen **tres poses** del personaje. Cada pose es un diccionario con dos claves:

- **`camera`**: Define la posición del ojo (`eye`), el punto de mira (`target`), el vector up y el campo de visión (`fov`).
- **`transforms`**: Diccionario que mapea el nombre de cada articulación a una matriz de rotación (o identidad). Estas rotaciones se combinan con las transformaciones base para dar la pose final.

#### Pose 1: `Spike_casual`

- **Cámara**: Vista lejana y frontal, FOV 45°.
- **Características**: Postura relajada. Brazos caídos, una mano en el muslo, cabeza ladeada, torso ligeramente inclinado.

#### Pose 2: `Spike_pelea`

- **Cámara**: Vista cercana y baja, FOV 100° (efecto gran angular).
- **Características**: Postura de combate. Torso inclinado hacia adelante, cabeza mirando hacia el frente, un brazo extendido como puñetazo y el otro cerca del rostro como defensa, piernas flexionadas en guardia.

#### Pose 3: `Gymbro`

- **Cámara**: Vista lateral alta, FOV 30° (teleobjetivo).
- **Características**: Postura de exhibición muscular (mostrando bíceps). Brazos flexionados, piernas separadas en pose de potencia.

### 3.8. Función `apply_pose`

```python
def apply_pose(pose_index):
    pose = poses[pose_index]
    transforms = pose["transforms"]

    graph.nodes["torso"]["transform"] = torso_transform @ transforms.get("torso", tr.identity())
    graph.nodes["cabeza"]["transform"] = cabeza_transform @ transforms["cabeza"]
    ...
```

- Recibe un índice (0, 1 o 2) y aplica la pose correspondiente.
- Para cada articulación, **multiplica** la transformación base (traslación/escala) con la rotación de la pose usando el operador `@` (multiplicación de matrices).
  - Ejemplo: `torso_transform @ transforms.get("torso", tr.identity())`.
  - Si la pose no define una transformación para cierta articulación, usa `tr.identity()` como valor por defecto.
- **Actualización de la cámara**:
  ```python
  camera = pose["camera"]
  new_view = tr.lookAt(camera["eye"], camera["target"], camera["up"])
  projection = tr.perspective(camera.get("fov"), float(width) / float(height), 0.1, 100.0)
  graph.register_view_transform(new_view)
  graph.set_global_attributes(projection=projection)
  ```
  - `tr.lookAt(...)`: Genera la matriz de vista a partir de la posición de la cámara, el punto de interés y el vector up.
  - `tr.perspective(...)`: Genera la matriz de proyección en perspectiva con el FOV, aspect ratio (ancho/alto), plano cercano (0.1) y plano lejano (100.0).
  - `register_view_transform(new_view)`: Establece la matriz de vista global del grafo de escena.
  - `set_global_attributes(projection=projection)`: Pasa la matriz de proyección como atributo global a todos los shaders.

### 3.9. Estado Inicial y Controles

```python
current_pose = 0
apply_pose(current_pose)
```

- Al iniciar, se aplica la primera pose (`Spike_casual`).

```python
@win.event
def on_key_press(symbol, modifiers):
    nonlocal current_pose
    if symbol == pyglet.window.key.SPACE:
        current_pose = (current_pose + 1) % 3
        apply_pose(current_pose)
```

- `on_key_press`: Evento de Pyglet que captura teclas presionadas.
- `nonlocal current_pose`: Permite modificar la variable definida en el scope exterior de la función `tarea`.
- **Barra espaciadora (`SPACE`)**: Cicla entre las 3 poses (0 → 1 → 2 → 0).

### 3.10. Bucle de Renderizado

```python
@win.event
def on_draw():
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glClearColor(0.12, 0.13, 0.15, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
    win.clear()
    graph.render()
```

- `glEnable(GL.GL_DEPTH_TEST)`: Activa el test de profundidad (Z-buffer), para que los objetos más cercanos a la cámara oculten a los más lejanos.
- `glClearColor(0.12, 0.13, 0.15, 1.0)`: Define un color de fondo gris azulado oscuro.
- `glClear(...)`: Limpia el framebuffer (color y profundidad) antes de dibujar el nuevo frame.
- `win.clear()`: Limpieza adicional de la ventana de Pyglet.
- `graph.render()`: Recorre el grafo de escena en orden DFS, calcula las transformaciones globales, establece los uniforms (`transform`, `view`, `projection`, `color`) y dibuja cada malla.

```python
pyglet.app.run()
```

- Inicia el loop principal de Pyglet, donde se procesan eventos (teclado, redibujado) y se mantiene la ventana abierta.

---

## Resumen de la Arquitectura

| Componente | Responsabilidad |
|------------|----------------|
| **Vertex Shader** | Transforma vértices de modelo → mundo → pantalla; prepara normales y colores. |
| **Fragment Shader** | Calcula iluminación ambiental + difusa para cada píxel. |
| **Scenegraph** | Organiza la escena en una jerarquía de nodos con transformaciones locales. |
| **Poses** | Conjunto de rotaciones por articulación que definen posturas del personaje. |
| **apply_pose** | Combina transformaciones base con rotaciones de pose y actualiza cámara. |
| **on_draw** | Limpia la pantalla y renderiza el grafo de escena. |
| **on_key_press** | Permite alternar entre poses con la barra espaciadora. |

Este diseño permite una separación clara entre la geometría (mallas `.off`), el aspecto visual (shaders GLSL) y la lógica de animación/poses (Python), facilitando la extensión del proyecto con nuevas articulaciones, poses o efectos de iluminación.
