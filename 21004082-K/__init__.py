"""
Tarea 9 — Escena Zuko vs. Ozai.

Punto de entrada del paquete 21004082-K. Integra todos los módulos de la
tarea (shaders, cámara, iluminación, entorno, Zuko, Ozai, director) en una
sola escena 3D que se ejecuta como::

    uv run python -m 21004082-K [--width 960 --height 720]

El módulo expone el comando Click ``tarea`` (consumido por ``__main__.py``)
y delega la lógica de orquestación al ``director``.

Pipeline de la escena
---------------------
1. Se construye un ``Scenegraph`` y se le asigna ``transform_parameter_name
   = "transform"`` (el vertex shader declara ``uniform mat4 transform``).
2. Se registra el pipeline ``"lit"`` cargando ``vertex_program.glsl`` y
   ``fragment_program.glsl`` desde el directorio del paquete.
3. Se invocan ``build_environment``, ``build_zuko`` y ``build_ozai`` para
   poblar la escena (todos reciben el nombre del pipeline).
4. ``update_scene`` y ``update_lighting_pipeline`` (director) se llaman una
   vez por frame; el director gestiona la cámara, las poses de los rigs y
   los uniforms de iluminación (PointLight + 2 SpotLights + Material).
5. SPACE pausa, R resetea el tiempo, ESC cierra la ventana.
"""

from __future__ import annotations

from pathlib import Path

import click
import numpy as np
import pyglet
from OpenGL import GL

from grafica.scenegraph import Scenegraph

# Módulos hermanos del paquete 21004082-K
from .camera import get_camera
from .environment import build_environment
from .zuko import build_zuko
from .ozai import build_ozai
from .director import update_scene, update_lighting_pipeline


# ---------------------------------------------------------------------------
# Constantes de la escena
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
VERTEX_PATH = HERE / "vertex_program.glsl"
FRAGMENT_PATH = HERE / "fragment_program.glsl"

PIPELINE_NAME = "lit"

# Duración total del timeline (segundos). El director congela la escena
# en el último frame cuando ``total_time`` supera este valor.
TOTAL_DURATION = 28.0

# Estado mutable de la línea de tiempo: el director lo lee cada frame.
STATE: dict = {
    "total_time": 0.0,
    "paused": False,
}


# ---------------------------------------------------------------------------
# Click: comando "tarea" (consumido por __main__.py)
# ---------------------------------------------------------------------------
@click.command("tarea", short_help="Escena 3D Zuko vs. Ozai (28 s)")
@click.option("--width", type=int, default=960, help="Ancho de la ventana en píxeles")
@click.option("--height", type=int, default=720, help="Alto de la ventana en píxeles")
def tarea(width: int, height: int) -> None:
    """Lanza la escena 3D Zuko vs. Ozai."""
    main(width, height)


# ---------------------------------------------------------------------------
# Construcción de la escena
# ---------------------------------------------------------------------------
def _build_scene(graph: Scenegraph) -> None:
    """
    Registra el pipeline ``"lit"`` y agrega el entorno, Zuko y Ozai al
    grafo. La cámara inicial se deja a cargo del primer frame del
    director para que el estado sea consistente con el resto del
    timeline.
    """
    # 1. Pipeline: shaders del paquete
    graph.load_and_register_pipeline(
        PIPELINE_NAME,
        str(VERTEX_PATH),
        str(FRAGMENT_PATH),
    )

    # 2. Módulos de la escena — todos comparten el mismo pipeline
    build_environment(graph, PIPELINE_NAME)
    build_zuko(graph, PIPELINE_NAME)
    build_ozai(graph, PIPELINE_NAME)

    # 3. Cámara inicial: shot 0 a t_local=0 (sobre el hombro de Zuko).
    #    El director la va a sobreescribir en el primer frame, pero la
    #    seteamos acá para que el grafo tenga una vista válida incluso
    #    si por alguna razón el primer frame no se ejecuta.
    #    Usamos aspect ratio 1.0 como default (el director lo actualiza
    #    al aspect real en el primer frame).
    view, projection = get_camera(0, 0.0, 960 / 720)
    graph.register_view_transform(view)
    graph.set_global_attributes(
        projection=projection,
        view_position=np.array([0.0, 0.0, 0.0], dtype=np.float32),
    )


# ---------------------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------------------
def main(width: int, height: int) -> None:
    """Abre la ventana, monta la escena y corre el app loop de pyglet."""
    # --- Scenegraph + pipeline + mallas ----------------------------------
    graph = Scenegraph("root")
    # El shader expone la matriz local con el nombre "transform"
    graph.transform_parameter_name = "transform"
    _build_scene(graph)

    # --- Ventana ---------------------------------------------------------
    window = pyglet.window.Window(width, height)

    # --- on_draw ---------------------------------------------------------
    @window.event
    def on_draw() -> None:
        # Fondo oscuro cálido (Nación del Fuego)
        GL.glClearColor(0.08, 0.04, 0.02, 1.0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        window.clear()
        graph.render()

    # --- on_key_press ----------------------------------------------------
    @window.event
    def on_key_press(symbol, modifiers) -> None:
        from pyglet.window import key
        if symbol == key.SPACE:
            STATE["paused"] = not STATE["paused"]
        elif symbol == key.R:
            STATE["total_time"] = 0.0
        elif symbol == key.ESCAPE:
            window.close()

    # --- update ----------------------------------------------------------
    def update(dt: float) -> None:
        if STATE["paused"]:
            return
        STATE["total_time"] = min(STATE["total_time"] + dt, TOTAL_DURATION)
        t = STATE["total_time"]
        update_scene(graph, t, width, height)
        update_lighting_pipeline(graph, t, pipeline_name=PIPELINE_NAME)

    # --- App loop --------------------------------------------------------
    pyglet.clock.schedule_interval(update, 1 / 60.0)
    pyglet.app.run(1 / 60.0)


if __name__ == "__main__":
    tarea()  # pragma: no cover
