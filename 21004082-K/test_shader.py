"""
Test de integración del pipeline de shaders (Tarea 4 — Escena Zuko vs. Ozai).

Carga los shaders de la tarea (vertex_program.glsl + fragment_program.glsl),
un cubo con color naranja forzado, una luz puntual cálida y dos spotlights
(torchas), y verifica que la escena se renderiza sin errores de shader.

Se cierra automáticamente a los 2 segundos.

Ejecutar:
    uv run python 21004082-K/test_shader.py
"""

from pathlib import Path

import numpy as np
import pyglet
import pyglet.gl as GL
import pyglet.graphics.shader

import grafica.transformations as tr
from grafica.scenegraph import Scenegraph


# --------------------------------------------------------------------------- #
# Rutas a los archivos del pipeline
# --------------------------------------------------------------------------- #
HERE = Path(__file__).resolve().parent
VERTEX_PATH = HERE / "vertex_program.glsl"
FRAGMENT_PATH = HERE / "fragment_program.glsl"
CUBE_PATH = Path("assets") / "cube.off"


# --------------------------------------------------------------------------- #
# Constantes de iluminación — tonos cálidos (Nación del Fuego)
# --------------------------------------------------------------------------- #
# PointLight cálida naranja en el techo (fuego central del escenario).
POINT_LIGHT = {
    "position": np.array([0.0, 4.0, 0.0], dtype=np.float32),
    "constant": 1.0,
    "linear": 0.09,
    "quadratic": 0.032,
    "ambient": np.array([0.25, 0.12, 0.05], dtype=np.float32),
    "diffuse": np.array([1.00, 0.55, 0.20], dtype=np.float32),
    "specular": np.array([1.00, 0.80, 0.50], dtype=np.float32),
}

# Dos spotlights (antorchas) iluminando desde los costados.
SPOT_LIGHT_0 = {
    "position": np.array([-2.0, 2.5, 2.0], dtype=np.float32),
    "direction": np.array([1.0, -0.6, -1.0], dtype=np.float32),
    "cutOff": np.cos(np.deg2rad(18.0)),
    "outerCutOff": np.cos(np.deg2rad(25.0)),
    "constant": 1.0,
    "linear": 0.09,
    "quadratic": 0.032,
    "ambient": np.array([0.10, 0.04, 0.02], dtype=np.float32),
    "diffuse": np.array([1.00, 0.45, 0.10], dtype=np.float32),
    "specular": np.array([1.00, 0.70, 0.30], dtype=np.float32),
}

SPOT_LIGHT_1 = {
    "position": np.array([2.0, 2.5, 2.0], dtype=np.float32),
    "direction": np.array([-1.0, -0.6, -1.0], dtype=np.float32),
    "cutOff": np.cos(np.deg2rad(18.0)),
    "outerCutOff": np.cos(np.deg2rad(25.0)),
    "constant": 1.0,
    "linear": 0.09,
    "quadratic": 0.032,
    "ambient": np.array([0.10, 0.04, 0.02], dtype=np.float32),
    "diffuse": np.array([1.00, 0.45, 0.10], dtype=np.float32),
    "specular": np.array([1.00, 0.70, 0.30], dtype=np.float32),
}

# Material del cubo: terminación metálica cálida.
MATERIAL = {
    "ambient": np.array([0.20, 0.10, 0.05], dtype=np.float32),
    "diffuse": np.array([0.80, 0.40, 0.20], dtype=np.float32),
    "specular": np.array([1.00, 0.80, 0.60], dtype=np.float32),
    "shininess": 32.0,
}

# Color forzado del cubo: naranja opaco [R, G, B, A] en uint8.
CUBE_COLOR = np.array([200, 100, 50, 255], dtype=np.uint8)


def _set_point_light(pipeline, prefix, light):
    """Sube los campos de un PointLight al shader.

    Los arrays de structs en GLSL quedan expuestos por pyglet con el nombre
    `pointLights[0].position`, etc. Pyglet hace la indirección del índice
    internamente, así que basta con pasar el field-name calificado.
    """
    try:
        pipeline[f"{prefix}.position"] = light["position"]
        pipeline[f"{prefix}.constant"] = light["constant"]
        pipeline[f"{prefix}.linear"] = light["linear"]
        pipeline[f"{prefix}.quadratic"] = light["quadratic"]
        pipeline[f"{prefix}.ambient"] = light["ambient"]
        pipeline[f"{prefix}.diffuse"] = light["diffuse"]
        pipeline[f"{prefix}.specular"] = light["specular"]
    except pyglet.graphics.shader.ShaderException as e:
        print(f"[WARN] no se pudo subir PointLight {prefix}: {e}")


def _set_spot_light(pipeline, prefix, light):
    """Sube los campos de un SpotLight al shader."""
    try:
        pipeline[f"{prefix}.position"] = light["position"]
        pipeline[f"{prefix}.direction"] = light["direction"]
        pipeline[f"{prefix}.cutOff"] = light["cutOff"]
        pipeline[f"{prefix}.outerCutOff"] = light["outerCutOff"]
        pipeline[f"{prefix}.constant"] = light["constant"]
        pipeline[f"{prefix}.linear"] = light["linear"]
        pipeline[f"{prefix}.quadratic"] = light["quadratic"]
        pipeline[f"{prefix}.ambient"] = light["ambient"]
        pipeline[f"{prefix}.diffuse"] = light["diffuse"]
        pipeline[f"{prefix}.specular"] = light["specular"]
    except pyglet.graphics.shader.ShaderException as e:
        print(f"[WARN] no se pudo subir SpotLight {prefix}: {e}")


def _set_material(pipeline, material):
    """Sube los campos del struct Material al shader."""
    try:
        pipeline["material.ambient"] = material["ambient"]
        pipeline["material.diffuse"] = material["diffuse"]
        pipeline["material.specular"] = material["specular"]
        pipeline["material.shininess"] = material["shininess"]
    except pyglet.graphics.shader.ShaderException as e:
        print(f"[WARN] no se pudo subir Material: {e}")


def main():
    width, height = 640, 480
    window = pyglet.window.Window(width, height, visible=True)
    aspect = width / height

    # ------------------------------------------------------------------ #
    # 1. Construir el Scenegraph y registrar el pipeline + la malla
    # ------------------------------------------------------------------ #
    graph = Scenegraph("root")
    # El shader de la tarea usa la uniform `transform` para la matriz
    # local, así que el scenegraph debe exponerla con ese nombre.
    graph.transform_parameter_name = "transform"

    graph.load_and_register_pipeline(
        "lit",
        str(VERTEX_PATH),
        str(FRAGMENT_PATH),
    )

    graph.load_and_register_mesh(
        "cube",
        str(CUBE_PATH),
        force_color=CUBE_COLOR,
    )

    # La malla cargada tiene un atributo `color` de 4 componentes (RGBA,
    # formato c4B del .off), pero el vertex shader declara `in vec3 color`.
    # Reescribimos el buffer a 3 componentes (RGB) con el color forzado
    # para que coincida con lo que el shader espera.
    cube_children = graph.meshes["cube"]["children"]
    if cube_children:
        color_attr = cube_children[0]["attributes"].get("color")
        if color_attr is not None and color_attr.size % 4 == 0:
            n_v = color_attr.size // 4
            colors_rgb = np.empty((n_v, 3), dtype=np.uint8)
            colors_rgb[:, 0] = CUBE_COLOR[0]
            colors_rgb[:, 1] = CUBE_COLOR[1]
            colors_rgb[:, 2] = CUBE_COLOR[2]
            cube_children[0]["attributes"]["color"] = colors_rgb.flatten()

    graph.add_object(
        "the_cube",
        "cube",
        "lit",
        parent="root",
        transform=tr.translate(0.0, 0.0, 0.0),
    )

    # ------------------------------------------------------------------ #
    # 2. Cámara y proyección
    # ------------------------------------------------------------------ #
    camera_position = np.array([2.0, 2.0, 3.0], dtype=np.float32)
    target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    up = np.array([0.0, 1.0, 0.0], dtype=np.float32)

    view = tr.lookAt(camera_position, target, up)
    projection = tr.perspective(45.0, aspect, 0.1, 10.0)

    graph.register_view_transform(view)

    # Atributos globales simples (matrices + posición de la cámara).
    graph.set_global_attributes(
        projection=projection,
        view_position=camera_position,
    )

    # ------------------------------------------------------------------ #
    # 3. Iluminación: PointLight + 2 SpotLights
    #    El scenegraph pasa el resto de uniforms simples por
    #    set_global_attributes, pero los arrays de structs no son
    #    amigables con esa ruta, así que los inyectamos directamente
    #    sobre el pipeline antes del primer render.
    # ------------------------------------------------------------------ #
    pipeline = graph.pipelines["lit"]
    _set_point_light(pipeline, "pointLights[0]", POINT_LIGHT)
    _set_spot_light(pipeline, "spotLights[0]", SPOT_LIGHT_0)
    _set_spot_light(pipeline, "spotLights[1]", SPOT_LIGHT_1)
    _set_material(pipeline, MATERIAL)

    # ------------------------------------------------------------------ #
    # 4. Draw: limpiar, depth test, render
    # ------------------------------------------------------------------ #
    @window.event
    def on_draw():
        GL.glClearColor(0.08, 0.04, 0.02, 1.0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        window.clear()
        try:
            graph.render()
        except pyglet.graphics.shader.ShaderException as e:
            print(f"[ERROR] ShaderException en render: {e}")
            window.close()
            raise

    # ------------------------------------------------------------------ #
    # 5. Cierre automático después de 2 s
    # ------------------------------------------------------------------ #
    def _close_after(_dt):
        print("OK")
        window.close()

    pyglet.clock.schedule_interval(_close_after, 2.0)
    pyglet.app.run()


if __name__ == "__main__":
    main()
