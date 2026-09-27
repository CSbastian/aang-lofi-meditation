"""Cámara orbital alrededor de Aang.

Gira en un círculo horizontal alrededor del target.
Controles:
    A / ← : rotar en sentido antihorario
    D / → : rotar en sentido horario
    Scroll: zoom in / out
    R: reset a la posición inicial.
"""

from __future__ import annotations

import math
import numpy as np

import grafica.transformations as tr


class OrbitCamera:
    """Cámara que orbita en un círculo horizontal alrededor de un punto fijo."""

    def __init__(
        self,
        target: np.ndarray,
        distance: float,
        height: float,
    ) -> None:
        self.target = np.asarray(target, dtype=np.float64)
        self.distance = distance
        self.height = height

        self._initial_distance = distance
        self._initial_height = height

        # Ángulo actual (0 = cámara en +Z mirando hacia el target)
        self.angle = 0.0
        self.orbit_speed = 1.5       # rad/s para A/D
        self.mouse_sensitivity = 0.005
        self.zoom_factor = 1.08       # por tick de scroll (> 1 = alejar)

        self.min_distance = max(distance * 0.1, 1.0)
        self.max_distance = distance * 4.0

        self._keys_held: set[int] = set()

    # ------------------------------------------------------------------
    # Geometría
    # ------------------------------------------------------------------

    def _get_eye(self) -> np.ndarray:
        x = self.target[0] + self.distance * math.sin(self.angle)
        y = self.target[1] + self.height
        z = self.target[2] + self.distance * math.cos(self.angle)
        return np.array([x, y, z], dtype=np.float64)

    def get_view_matrix(self) -> np.ndarray:
        eye = self._get_eye().astype(np.float32)
        tgt = self.target.astype(np.float32)
        up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        return tr.lookAt(eye, tgt, up)

    def get_position(self) -> np.ndarray:
        return self._get_eye()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        KEY_A = 97
        KEY_D = 100
        KEY_LEFT = 65361
        KEY_RIGHT = 65363

        if KEY_A in self._keys_held or KEY_LEFT in self._keys_held:
            self.angle -= self.orbit_speed * dt
        if KEY_D in self._keys_held or KEY_RIGHT in self._keys_held:
            self.angle += self.orbit_speed * dt

    # ------------------------------------------------------------------
    # Teclado
    # ------------------------------------------------------------------

    def on_key_press(self, symbol: int) -> None:
        KEY_A = 97
        KEY_D = 100
        KEY_LEFT = 65361
        KEY_RIGHT = 65363
        if symbol in (KEY_A, KEY_D, KEY_LEFT, KEY_RIGHT):
            self._keys_held.add(symbol)

    def on_key_release(self, symbol: int) -> None:
        self._keys_held.discard(symbol)

    # ------------------------------------------------------------------
    # Mouse
    # ------------------------------------------------------------------

    def on_mouse_scroll(
        self, x: int, y: int, scroll_x: float, scroll_y: float
    ) -> None:
        if scroll_y > 0:
            self.distance /= self.zoom_factor
        elif scroll_y < 0:
            self.distance *= self.zoom_factor
        self.distance = float(np.clip(self.distance, self.min_distance, self.max_distance))

    def on_mouse_drag(
        self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int
    ) -> None:
        # Arrastrar con botón izquierdo para rotar manualmente
        if buttons & 1:
            self.angle += dx * self.mouse_sensitivity

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        self.angle = 0.0
        self.distance = self._initial_distance
        self.height = self._initial_height
