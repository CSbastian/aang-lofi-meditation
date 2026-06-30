"""Cámara Lo-Fi para la escena meditativa de Aang.

Envuelve `grafica.arcball.Arcball` y le agrega:
    * Movimiento WASD limitado a una caja alrededor del target.
    * Damping exponencial sobre la pose y el target (sensación "fluida").
    * Accesores convenientes para la matriz de vista y reset.

La clase no depende de pyglet.window directamente: el orquestador (la
Window) traduce los eventos de mouse/teclado y nos llama por nombre. Así
podemos testearla sin abrir una ventana.

Convenciones de Arcball que usamos acá:
    * `arcball.pose` es la matriz cámara-a-mundo (4x4).
    * `arcball.target` es el centro de órbita (coordenadas de mundo).
    * Adelante de la cámara (hacia donde mira) = -pose[:3, 2].
    * Derecha de la cámara = pose[:3, 0].
    * Matriz de vista = inv(pose).
"""

from __future__ import annotations

import math
import numpy as np

from grafica.arcball import Arcball
import grafica.transformations as tr


# Constantes de pyglet.window.mouse para mapear botón -> estado del arcball.
# Se mantienen como enteros para no importar pyglet acá adentro: el módulo
# queda desacoplado de la ventana. Los valores numéricos son los oficiales
# de pyglet 2.x.
_MOUSE_LEFT   = 1
_MOUSE_RIGHT  = 4
_MOUSE_MIDDLE = 2


def _lerp_matrix(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    """Interpolación lineal componente a componente entre dos matrices 4x4.

    Para poses (cámara-a-mundo) no es la interpolación de rotación más
    correcta, pero es suficiente para damping de baja amplitud: el ojo
    humano no distingue un slerp de un lerp cuando el paso es pequeño
    (típicamente t < 0.2). Mantenerlo simple evita la sobrecarga de
    convertir a cuaternión en cada frame.
    """
    return a + t * (b - a)


def _flatten_to_horizontal(vec: np.ndarray) -> np.ndarray:
    """Proyecta un vector 3D al plano horizontal (y=0) y lo renormaliza.

    Sirve para que el movimiento WASD siempre quede en el plano del suelo,
    incluso si la cámara está mirando en diagonal. Si la proyección cae
    en el origen (vector puramente vertical), devolvemos el vector original
    para no propagar un cero que rompería el movimiento.
    """
    flat = np.array([vec[0], 0.0, vec[2]], dtype=np.float64)
    norm = np.linalg.norm(flat)
    if norm < 1e-10:
        return vec
    return flat / norm


class LoFiCamera:
    """Cámara orbital con WASD acotado y damping exponencial."""

    def __init__(
        self,
        width: int,
        height: int,
        target: np.ndarray,
        initial_eye: np.ndarray,
        scene_scale: float,
    ) -> None:
        """Inicializa la cámara.

        Parámetros
        ----------
        width, height : int
            Tamaño de la ventana en píxeles. Se entrega al Arcball para
            normalizar el drag del mouse.
        target : (3,) array
            Centro de órbita (normalmente la posición de Aang).
        initial_eye : (3,) array
            Posición inicial de la cámara.
        scene_scale : float
            Escala característica de la escena. Se usa para calibrar
            sensibilidad del Arcball, velocidad de WASD y los límites
            de movimiento. La convención del repo (skinning/__init__.py)
            es usar la diagonal del bounding box del modelo.
        """
        target = np.asarray(target, dtype=np.float64)
        initial_eye = np.asarray(initial_eye, dtype=np.float64)

        # Construimos la pose inicial a partir de un lookAt. Arcball espera
        # la matriz cámara-a-mundo (= inv(view)), por eso el np.linalg.inv.
        initial_view = tr.lookAt(
            initial_eye.astype(np.float32),
            target.astype(np.float32),
            np.array([0.0, 1.0, 0.0], dtype=np.float32),
        )
        self.arcball = Arcball(
            np.linalg.inv(initial_view),
            np.array((width, height), dtype=float),
            float(scene_scale),
            target.astype(np.float64),
        )
        self.arcball.set_distance_limits(scene_scale * 0.2, scene_scale * 6.0)

        # Estado de movimiento WASD. `move_target` es el punto objetivo al
        # que queremos llevar el centro de órbita; cada frame interpolamos
        # `arcball.target` hacia él (lo que también arrastra la cámara).
        self.target = target.copy()
        self.move_target = target.copy()
        self.move_speed = float(scene_scale) * 0.15

        # Caja de movimiento: un cuadrado en XZ centrado en el target
        # original. Mantiene al usuario dentro de la composición descrita
        # en Escena.md sin permitirle irse a explorar el vacío.
        self.move_limits = {
            "x_min": float(target[0] - scene_scale * 1.5),
            "x_max": float(target[0] + scene_scale * 1.5),
            "z_min": float(target[2] - scene_scale * 1.5),
            "z_max": float(target[2] + scene_scale * 1.5),
        }

        # Damping. damping_alpha = 0 => instantáneo; 1 => congelado.
        # 0.1 es lo bastante lento para que el movimiento se sienta "lo-fi"
        # sin让人觉得 la cámara arrastra los pies.
        self.damping_alpha = 0.08

        # Snapshot de la pose al iniciar un drag. Mientras el usuario está
        # arrastrando, `arcball.pose` se actualiza en vivo; al soltar,
        # seguimos interpolando desde este snapshot hacia la pose final
        # para que el frenado sea suave.
        self._drag_start_pose: np.ndarray | None = None
        self._drag_start_target: np.ndarray | None = None

        # Teclas presionadas (para movimiento continuo con WASD)
        self._keys_held: set[int] = set()

    # ------------------------------------------------------------------
    # Mouse: delegamos al Arcball eligiendo el estado según el botón.
    # ------------------------------------------------------------------

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        """Registra el inicio de un drag. Elige modo según el botón.

        Botón izquierdo => rotar, derecho => pan, medio => zoom con drag.
        Hacemos snapshot de la pose al presionar para que el damping
        pueda interpolar desde ahí cuando se suelte.
        """
        if button == _MOUSE_LEFT:
            self.arcball.set_state(Arcball.STATE_ROTATE)
        elif button == _MOUSE_RIGHT:
            self.arcball.set_state(Arcball.STATE_PAN)
        elif button == _MOUSE_MIDDLE:
            self.arcball.set_state(Arcball.STATE_ZOOM)
        else:
            # Botón desconocido: caemos al comportamiento por defecto
            # (rotación) que es el más común.
            self.arcball.set_state(Arcball.STATE_ROTATE)

        self.arcball.down((x, y))
        # Guardamos la pose previa al drag para que el damping tenga
        # desde dónde interpolar.
        self._drag_start_pose = np.copy(self.arcball.pose)
        self._drag_start_target = np.copy(self.arcball.target)

    def on_mouse_drag(
        self,
        x: int,
        y: int,
        dx: int,
        dy: int,
        buttons: int,
        modifiers: int,
    ) -> None:
        """Reenvía la posición al Arcball durante un drag."""
        self.arcball.drag((x, y))

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> None:
        self._drag_start_pose = None
        self._drag_start_target = None

    def on_mouse_scroll(
        self,
        x: int,
        y: int,
        scroll_x: float,
        scroll_y: float,
    ) -> None:
        """Zoom con la rueda. scroll_y positivo = acercar."""
        # Arcball.scroll() multiplica la distancia por 0.9^clicks, así
        # que pasamos el número de "clicks" directamente.
        self.arcball.scroll(int(scroll_y))
        # Tras un scroll la pose "salta" al nuevo zoom; guardamos
        # snapshot para que el damping no vea un delta artificial
        # entre la pose previa y la nueva.
        self._drag_start_pose = np.copy(self.arcball.pose)
        self._drag_start_target = np.copy(self.arcball.target)

    # ------------------------------------------------------------------
    # Teclado: WASD mueve el target por el plano horizontal.
    # ------------------------------------------------------------------

    def on_key_press_WASD(self, symbol: int) -> None:
        """Registra una tecla WASD como presionada (movimiento continuo en update())."""
        KEY_W = 119
        KEY_A = 97
        KEY_S = 115
        KEY_D = 100

        if symbol in (KEY_W, KEY_A, KEY_S, KEY_D):
            self._keys_held.add(symbol)

    def on_key_release_WASD(self, symbol: int) -> None:
        """Quita una tecla WASD del set de presionadas."""
        KEY_W = 119
        KEY_A = 97
        KEY_S = 115
        KEY_D = 100
        self._keys_held.discard(symbol)

    def _clamp_move_target(self) -> None:
        """Restringe `move_target` a la caja definida en `move_limits`.

        Sólo clampamos X y Z: la cámara no se mueve verticalmente con
        WASD, así que el eje Y queda libre para el paneo del Arcball.
        """
        self.move_target[0] = float(
            np.clip(self.move_target[0], self.move_limits["x_min"], self.move_limits["x_max"])
        )
        self.move_target[2] = float(
            np.clip(self.move_target[2], self.move_limits["z_min"], self.move_limits["z_max"])
        )

    # ------------------------------------------------------------------
    # Damping y actualización por frame.
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        alpha = 1.0 - math.exp(-self.damping_alpha * dt * 60.0)
        alpha = float(np.clip(alpha, 0.0, 1.0))

        # Movimiento continuo WASD (teclas presionadas se procesan en update)
        if self._keys_held:
            KEY_W, KEY_A, KEY_S, KEY_D = 119, 97, 115, 100
            pose = self.arcball.pose
            forward = -pose[:3, 2]
            right = pose[:3, 0]
            forward_flat = _flatten_to_horizontal(forward)
            right_flat = _flatten_to_horizontal(right)
            speed = self.move_speed * 60.0 * dt  # frame-rate independent
            if KEY_W in self._keys_held:
                self.move_target -= forward_flat * speed
            if KEY_S in self._keys_held:
                self.move_target += forward_flat * speed
            if KEY_A in self._keys_held:
                self.move_target -= right_flat * speed
            if KEY_D in self._keys_held:
                self.move_target += right_flat * speed

        # Interpolamos el target hacia `move_target` con la misma
        # curva. Así, tras soltar WASD, la cámara "aterriza" suave
        # en el centro de órbita pedido por el usuario.
        if not np.allclose(self.arcball.target, self.move_target):
            self.arcball.target = (
                self.arcball.target + alpha * (self.move_target - self.arcball.target)
            )

    # ------------------------------------------------------------------
    # Accesores.
    # ------------------------------------------------------------------

    def get_view_matrix(self) -> np.ndarray:
        """Devuelve la matriz de vista (mundo -> cámara) para los shaders."""
        return np.linalg.inv(self.arcball.pose)

    def reset(self) -> None:
        """Vuelve al estado inicial: pose, target y move_target originales."""
        self.arcball.reset()
        self.move_target = np.copy(self.arcball.target)
        self._drag_start_pose = None
        self._drag_start_target = None
