"""
Sistema de cámara cinematográfico para la escena Zuko vs Ozai.

Define 7 tomas (shots) con matrices de vista y proyección.
Se usa interpolación lineal dentro de las tomas 1 y 5 (zoom).
Cortes duros entre tomas.

Referencias:
    - grafica.transformations.lookAt  -> matriz de vista 4x4
    - grafica.transformations.perspective -> matriz de proyección 4x4
"""

import numpy as np
import grafica.transformations as tr


def lerp(a, b, t):
    """Interpolación lineal entre a y b por factor t (0 = a, 1 = b)."""
    return a + (b - a) * t


# Vector up constante para todas las tomas
_UP = np.array([0, 1, 0], dtype=np.float32)

# ---------------------------------------------------------------------------
# Definición de las 7 tomas
# Cada toma es un diccionario con:
#   - type:       descripción del tipo de plano
#   - at:         punto al que mira la cámara (siempre fijo dentro de la toma)
#   - interpolate: True si la toma requiere interpolación (zoom)
#
# Tomas estáticas: eye, fov  (valores fijos)
# Tomas con zoom:  eye_start, eye_end, fov_start, fov_end
# ---------------------------------------------------------------------------

SHOTS = [
    # Toma 0 — 0-1s  | Plano general (sobre el hombro de Zuko)
    {
        "type": "plano_general_hombro",
        "eye": np.array([-1.5, 1.5, 3.5], dtype=np.float32),
        "at": np.array([0.0, 1.2, 0.0], dtype=np.float32),
        "fov": 45.0,
    },
    # Toma 1 — 1-7s  | Zoom in lento (plano medio → primer plano)
    {
        "type": "zoom_in",
        "interpolate": True,
        "eye_start": np.array([-1.5, 1.5, 3.5], dtype=np.float32),
        "eye_end": np.array([-0.6, 1.6, 1.8], dtype=np.float32),
        "at": np.array([0.0, 1.5, 0.0], dtype=np.float32),
        "fov_start": 45.0,
        "fov_end": 55.0,
    },
    # Toma 2 — 7-11s | Plano medio (perspectiva de Ozai)
    {
        "type": "plano_medio_ozai",
        "eye": np.array([0.0, 2.0, 1.0], dtype=np.float32),
        "at": np.array([0.0, 1.5, 3.0], dtype=np.float32),
        "fov": 50.0,
    },
    # Toma 3 — 11-16s | Primer plano (Ozai)
    {
        "type": "primer_plano_ozai",
        "eye": np.array([0.5, 1.8, -2.5], dtype=np.float32),
        "at": np.array([0.0, 1.8, -3.5], dtype=np.float32),
        "fov": 35.0,
    },
    # Toma 4 — 16-20s | Perfil izquierdo de Zuko
    {
        "type": "perfil_zuko",
        "eye": np.array([-3.0, 1.5, 2.0], dtype=np.float32),
        "at": np.array([-0.5, 1.5, 1.5], dtype=np.float32),
        "fov": 40.0,
    },
    # Toma 5 — 20-25s | Plano general — zoom out leve
    {
        "type": "zoom_out",
        "interpolate": True,
        "eye_start": np.array([-2.0, 1.6, 3.5], dtype=np.float32),
        "eye_end": np.array([-2.5, 1.5, 4.0], dtype=np.float32),
        "at": np.array([0.0, 1.2, 0.0], dtype=np.float32),
        "fov_start": 50.0,
        "fov_end": 42.0,
    },
    # Toma 6 — 25-28s | Plano contrapicado (low-angle)
    {
        "type": "contrapicado",
        "eye": np.array([-1.0, 0.3, 2.0], dtype=np.float32),
        "at": np.array([-0.5, 1.8, 1.0], dtype=np.float32),
        "fov": 55.0,
    },
]


def get_camera(shot_index, t_local, aspect):
    """
    Calcula las matrices de vista y proyección para una toma dada.

    Parameters
    ----------
    shot_index : int
        Índice de la toma (0-6).
    t_local : float
        Tiempo normalizado dentro de la toma [0, 1].
    aspect : float
        Relación de aspecto (ancho / alto) de la ventana.

    Returns
    -------
    view : np.ndarray (4x4, float32)
        Matriz de vista (lookAt).
    projection : np.ndarray (4x4, float32)
        Matriz de proyección en perspectiva.
    """
    shot = SHOTS[shot_index]

    if shot.get("interpolate"):
        eye = lerp(shot["eye_start"], shot["eye_end"], t_local)
        fov = lerp(shot["fov_start"], shot["fov_end"], t_local)
    else:
        eye = shot["eye"]
        fov = shot["fov"]

    at = shot["at"]

    view = tr.lookAt(eye, at, _UP)
    projection = tr.perspective(fov, aspect, 0.1, 100.0)

    return view, projection
