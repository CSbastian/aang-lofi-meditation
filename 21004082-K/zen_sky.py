"""
Cielo estilo zen/japones con ciclo dia-noche.

Genera una textura equirectangular 2K con gradientes suaves,
montanas lejanas, y elementos sutiles. Implementa el ciclo
dia-noche mezclando 4 texturas (amanecer, dia, atardecer, noche).
"""

import math
import os

import numpy as np
from PIL import Image

import pyglet
import pyglet.gl as GL
from pathlib import Path

from grafica.utils import load_pipeline


# ---------------------------------------------------------------------------
# Sky parameters
# ---------------------------------------------------------------------------

# Tamano de la textura equirectangular
TEXTURE_WIDTH = 2048
TEXTURE_HEIGHT = 1024

# Duracion del ciclo dia-noche en segundos
CYCLE_DURATION = 30.0

# Alturas en la imagen equirectangular (0 = cenit, 0.5 = horizonte, 1 = nadir)
HORIZON_Y = 0.5

# Colores por momento del dia (RGBA 0-255)
# Formato: (top_r, top_g, top_b, bottom_r, bottom_g, bottom_b)
DAWN = {
    "top":    (180, 130, 130),   # rosa palido arriba
    "horizon": (220, 160, 120),  # melocoton
    "bottom":  (160, 120, 110),  # tierra palida
}

DAY = {
    "top":    (100, 150, 220),   # azul cielo
    "horizon": (200, 220, 250),  # blanco azulado
    "bottom":  (180, 200, 230),  # azul palido
}

DUSK = {
    "top":    (80, 60, 100),     # purpura oscuro
    "horizon": (240, 150, 80),   # naranja brillante
    "bottom":  (120, 70, 50),    # marron palido
}

NIGHT = {
    "top":    (8, 8, 25),        # azul oscuro
    "horizon": (20, 25, 45),     # azul medio
    "bottom":  (15, 20, 35),     # azul palido
}


def lerp_color(c1, c2, t):
    """Interpola entre dos colores (tuplas RGB)."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def get_mood_colors(t01):
    """Devuelve el color del cielo segun el momento del dia (0-1)."""
    # t01: 0 = amanecer, 0.25 = dia, 0.5 = atardecer, 0.75-1 = noche
    if t01 < 0.25:
        # Transicion amanecer -> dia
        local_t = t01 / 0.25
        return {
            "top": lerp_color(DAWN["top"], DAY["top"], local_t),
            "horizon": lerp_color(DAWN["horizon"], DAY["horizon"], local_t),
            "bottom": lerp_color(DAWN["bottom"], DAY["bottom"], local_t),
        }
    elif t01 < 0.5:
        # Transicion dia -> atardecer
        local_t = (t01 - 0.25) / 0.25
        return {
            "top": lerp_color(DAY["top"], DUSK["top"], local_t),
            "horizon": lerp_color(DAY["horizon"], DUSK["horizon"], local_t),
            "bottom": lerp_color(DAY["bottom"], DUSK["bottom"], local_t),
        }
    elif t01 < 0.75:
        # Transicion atardecer -> noche
        local_t = (t01 - 0.5) / 0.25
        return {
            "top": lerp_color(DUSK["top"], NIGHT["top"], local_t),
            "horizon": lerp_color(DUSK["horizon"], NIGHT["horizon"], local_t),
            "bottom": lerp_color(DUSK["bottom"], NIGHT["bottom"], local_t),
        }
    else:
        # Transicion noche -> amanecer (siguiente ciclo)
        local_t = (t01 - 0.75) / 0.25
        return {
            "top": lerp_color(NIGHT["top"], DAWN["top"], local_t),
            "horizon": lerp_color(NIGHT["horizon"], DAWN["horizon"], local_t),
            "bottom": lerp_color(NIGHT["bottom"], DAWN["bottom"], local_t),
        }


def generate_sky_texture(time_01):
    """Genera la textura del cielo segun el momento del dia.

    Args:
        time_01: float en [0, 1] que indica el momento del dia
                 0 = amanecer, 0.25 = dia, 0.5 = atardecer, 0.75-1 = noche

    Returns:
        Image (PIL) equirectangular 2048x1024
    """
    colors = get_mood_colors(time_01)
    width, height = TEXTURE_WIDTH, TEXTURE_HEIGHT

    # Crear gradiente vertical
    arr = np.zeros((height, width, 3), dtype=np.uint8)

    for y in range(height):
        # Mapear y a angulo polar: 0 (top) = 90deg, height/2 = 0deg, height (bottom) = -90deg
        t = y / height
        # Convertir a angulo (de -PI/2 a PI/2)
        theta = (t - 0.5) * math.pi
        # t=0: theta=PI/2 (arriba), t=0.5: theta=0 (horizonte), t=1: theta=-PI/2 (abajo)

        if t < HORIZON_Y:
            # Entre top y horizonte
            local = t / HORIZON_Y
            local = local ** 0.7  # ajustar curva para que el horizonte sea mas amplio
            color = lerp_color(colors["top"], colors["horizon"], local)
        else:
            # Entre horizonte y bottom
            local = (t - HORIZON_Y) / (1.0 - HORIZON_Y)
            local = local ** 0.9
            color = lerp_color(colors["horizon"], colors["bottom"], local)

        arr[y, :] = color

    # Agregar montanas lejanas (silueta oscura en el horizonte)
    mountain_color = (30, 25, 35)
    for x in range(width):
        # Onda suave para las montanas
        u = x / width
        # Multi-octava simple
        h = 0
        h += 0.5 * math.sin(u * 12 * math.pi)
        h += 0.3 * math.sin(u * 25 * math.pi + 1.3)
        h += 0.2 * math.sin(u * 50 * math.pi + 2.6)
        h = h * 0.02  # altura maxima pequena
        # Posicion de las montanas en el horizonte
        mountain_y = int(height * HORIZON_Y + h * height)
        # Oscurecer las montanas segun la hora
        darkness = 0.4 if time_01 < 0.5 else 0.7
        for dy in range(mountain_y, min(height, mountain_y + int(height * 0.05))):
            mountain_t = (dy - mountain_y) / (height * 0.05)
            m_color = lerp_color(arr[dy, x].tolist(),
                                 [int(c * (1 - darkness) + mountain_color[i] * darkness)
                                  for i, c in enumerate(arr[dy, x].tolist())],
                                 mountain_t * 0.5)
            arr[dy, x] = m_color

    # Agregar luna (visible en transiciones de noche y amanecer)
    if time_01 > 0.5 or time_01 < 0.15:
        moon_x = int(width * 0.7)
        moon_y = int(height * 0.2)
        moon_radius = 30
        moon_color = (240, 235, 220)
        for dy in range(-moon_radius, moon_radius + 1):
            for dx in range(-moon_radius, moon_radius + 1):
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < moon_radius:
                    # alpha segun distancia
                    alpha = max(0, 1 - dist / moon_radius)
                    y, x = moon_y + dy, moon_x + dx
                    if 0 <= y < height and 0 <= x < width:
                        for i in range(3):
                            arr[y, x, i] = int(arr[y, x, i] * (1 - alpha) + moon_color[i] * alpha)

    return Image.fromarray(arr, "RGB")


def generate_all_moods():
    """Genera las 4 texturas base (amanecer, dia, atardecer, noche) + 8 intermedias
    para tener transiciones suaves al interpolar.

    Returns:
        dict con keys 'dawn', 'day', 'dusk', 'night' y 'interp_<i>' con texturas PIL
    """
    textures = {
        "dawn":  generate_sky_texture(0.0),
        "day":   generate_sky_texture(0.25),
        "dusk":  generate_sky_texture(0.5),
        "night": generate_sky_texture(0.75),
    }
    # Generar 8 frames intermedios para suavizar las transiciones
    for i in range(1, 9):
        t = i / 8.0
        textures[f"interp_{i}"] = generate_sky_texture(t)
    return textures


def upload_sky_textures(frames):
    """Sube las texturas a GPU y devuelve un dict {key: texture_id}."""
    from grafica.textures import texture_2D_setup
    texture_ids = {}
    for key, image in frames.items():
        if image.mode != "RGB":
            image = image.convert("RGB")
        texture_id = texture_2D_setup(image, flip_top_bottom=True)
        texture_ids[key] = texture_id
    return texture_ids


def generate_sphere_geometry_equirect(radius, slices=64, stacks=32):
    """Genera una esfera con UVs equirectangulares.

    UV mapping: u=0 es theta=0, u=1 es theta=2pi (longitud)
                v=0 es phi=pi/2 (polo norte), v=1 es phi=-pi/2 (polo sur)
    """
    positions = []
    uvs = []
    indices = []

    for i in range(stacks + 1):
        v = i / stacks
        phi = math.pi * (1 - v)  # de pi (norte) a 0 (sur)
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
            # UV equirectangular
            uvs.append((u, v))

    for i in range(stacks):
        for j in range(slices):
            a = i * (slices + 1) + j
            b = a + slices + 1
            indices.extend([a, b, a + 1])
            indices.extend([a + 1, b, b + 1])

    return (np.array(positions, dtype=np.float32),
            np.array(uvs, dtype=np.float32),
            np.array(indices, dtype=np.uint32))


def setup_zen_skybox(pipeline):
    """Crea el skybox zen con texturas generadas.

    Returns:
        dict con vl (vertex_list), pipeline, texture_ids
    """
    # Generar las texturas
    frames = generate_all_moods()
    texture_ids = upload_sky_textures(frames)

    # Crear geometria de esfera con UVs
    positions, uvs, indices = generate_sphere_geometry_equirect(100.0)

    # Crear vertex list
    vl = pipeline.vertex_list_indexed(
        len(positions), GL.GL_TRIANGLES, indices.tolist()
    )
    vl.position[:] = positions.flatten()
    vl.uv[:] = uvs.flatten()

    # Guardar la lista de frames en orden
    frame_keys = ["dawn", "interp_1", "interp_2", "interp_3",
                  "day", "interp_4", "interp_5", "interp_6",
                  "dusk", "interp_7", "interp_8", "night"]

    return {"vl": vl, "pipeline": pipeline, "texture_ids": texture_ids,
            "frame_keys": frame_keys}


def render_zen_skybox(renderer, view_matrix, projection_matrix, time):
    """Renderiza el skybox con interpolacion dia-noche."""
    pipeline = renderer["pipeline"]
    vl = renderer["vl"]
    texture_ids = renderer["texture_ids"]
    frame_keys = renderer["frame_keys"]

    # Calcular el frame actual
    t01 = (time % CYCLE_DURATION) / CYCLE_DURATION
    # 12 frames en el ciclo (4 principales + 8 intermedios)
    frame_index = t01 * 12
    idx_low = int(frame_index) % 12
    idx_high = (idx_low + 1) % 12
    blend = frame_index - int(frame_index)

    # Calcular la matriz de vista sin traslación
    view_no_translation = view_matrix.copy()
    view_no_translation[0, 3] = 0.0
    view_no_translation[1, 3] = 0.0
    view_no_translation[2, 3] = 0.0

    # Renderizar el frame bajo
    tex_low = texture_ids[frame_keys[idx_low]]
    tex_high = texture_ids[frame_keys[idx_high]]

    pipeline.use()
    pipeline["u_projection"] = projection_matrix.reshape(16, 1, order="F")
    pipeline["u_view"] = view_no_translation.reshape(16, 1, order="F")

    # Renderizar dos veces con alpha blending para crossfade
    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glDepthMask(GL.GL_FALSE)
    GL.glDisable(GL.GL_CULL_FACE)

    # Frame bajo (full opacity)
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex_low)
    pipeline["u_blend"] = 0.0
    vl.draw(GL.GL_TRIANGLES)

    # Frame alto (con alpha segun blend)
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex_high)
    pipeline["u_blend"] = float(blend)
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    vl.draw(GL.GL_TRIANGLES)
    GL.glDisable(GL.GL_BLEND)

    GL.glEnable(GL.GL_CULL_FACE)
    GL.glDepthMask(GL.GL_TRUE)
    GL.glEnable(GL.GL_DEPTH_TEST)
