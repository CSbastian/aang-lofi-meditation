"""
Skydome: cielo nocturno con estrellas procedurales titilando.

Genera una esfera grande alrededor de la camara. El fragment shader
crea el efecto de cielo nocturno con estrellas usando funciones de hash
(deterministicas, sin texturas externas).

Parametros editables abajo.
"""

import math

import numpy as np
import pyglet
import pyglet.gl as GL
from pathlib import Path

from grafica.utils import load_pipeline


# ---------------------------------------------------------------------------
# Skydome parameters
# ---------------------------------------------------------------------------

# Colors del cielo (gradiente vertical)
SKY_COLOR_TOP_R = 0.005         # casi negro (cénit)
SKY_COLOR_TOP_G = 0.005
SKY_COLOR_TOP_B = 0.02          # leve tinte azul
SKY_COLOR_BOTTOM_R = 0.02       # horizonte un poco más claro
SKY_COLOR_BOTTOM_G = 0.02
SKY_COLOR_BOTTOM_B = 0.04

SKY_RADIUS = 15.0               # radio del skydome (debe ser menor que el far plane)

# Estrellas
STAR_DENSITY = 100.0            # densidad de celdas (mayor = más estrellas)
STAR_BRIGHTNESS = 1.5           # brillo base de las estrellas

# Ciclo dia-noche
CYCLE_DURATION = 30.0           # segundos por ciclo completo


def generate_sphere_geometry(radius, slices=48, stacks=24):
    """Genera los vertices e indices de una esfera UV.

    Returns:
        positions: array (N, 3) de posiciones
        indices: array (M,) de indices para GL_TRIANGLES
    """
    positions = []
    indices = []

    for i in range(stacks + 1):
        v = i / stacks
        phi = math.pi * v  # 0 (norte) a pi (sur)
        sin_phi = math.sin(phi)
        cos_phi = math.cos(phi)

        for j in range(slices + 1):
            u = j / slices
            theta = 2.0 * math.pi * u
            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)

            x = radius * sin_phi * cos_theta
            y = radius * cos_phi
            z = radius * sin_phi * sin_theta
            positions.append((x, y, z))

    # Indices: dos triangulos por quad
    for i in range(stacks):
        for j in range(slices):
            a = i * (slices + 1) + j
            b = a + slices + 1
            indices.extend([a, b, a + 1])
            indices.extend([a + 1, b, b + 1])

    return (np.array(positions, dtype=np.float32),
            np.array(indices, dtype=np.uint32))


def setup_skybox(pipeline):
    """Crea el skydome: esfera con vertex list en el pipeline.

    Returns:
        dict con vl (vertex_list) y pipeline
    """
    positions, indices = generate_sphere_geometry(SKY_RADIUS)

    # Vertex list indexed
    vl = pipeline.vertex_list_indexed(
        len(positions), GL.GL_TRIANGLES, indices.tolist()
    )
    vl.position[:] = positions.flatten()

    return {"vl": vl, "pipeline": pipeline}


def render_skybox(renderer, view_matrix, projection_matrix, time=0.0):
    """Renderiza el skydome con el shader procedural."""
    pipeline = renderer["pipeline"]
    vl = renderer["vl"]

    # Calcular la matriz de vista sin traslación (para que el skydome siga a la camara)
    # En una view matrix de OpenGL: view = T * R, donde la traslacion esta
    # en la columna view[0:3, 3]. Hay que ponerla en cero para que el
    # skydome siempre se vea desde el mismo angulo (sensacion de infinito).
    view_no_translation = view_matrix.copy()
    view_no_translation[0, 3] = 0.0
    view_no_translation[1, 3] = 0.0
    view_no_translation[2, 3] = 0.0

    pipeline.use()
    pipeline["u_projection"] = projection_matrix.reshape(16, 1, order="F")
    pipeline["u_view"] = view_no_translation.reshape(16, 1, order="F")
    pipeline["u_time"] = float(time)
    pipeline["u_cycle_duration"] = float(CYCLE_DURATION)
    pipeline["u_star_density"] = float(STAR_DENSITY)
    pipeline["u_star_brightness"] = float(STAR_BRIGHTNESS)

    # Desactivar depth test para que el cielo siempre se vea detras de todo
    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glDepthMask(GL.GL_FALSE)
    # Renderizar el skydome con su cara hacia adentro (culling desactivado)
    GL.glDisable(GL.GL_CULL_FACE)
    vl.draw(GL.GL_TRIANGLES)
    GL.glEnable(GL.GL_CULL_FACE)
    GL.glDepthMask(GL.GL_TRUE)
    GL.glEnable(GL.GL_DEPTH_TEST)
