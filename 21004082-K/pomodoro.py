"""Timer Pomodoro con la imagen del loto blanco como fondo visual.

Ciclo: 25 minutos de trabajo -> 5 minutos de descanso -> repetir.
Controles (teclado):
    P  : pausar / reanudar
    N  : saltar al siguiente periodo (work <-> rest)

El modulo es autocontenido: carga la textura del loto al instanciarse,
lleva el estado del timer, actualiza con un dt, y sabe dibujarse
encima de la escena 3D usando `ui_overlay`.
"""

from __future__ import annotations

from pathlib import Path

import pyglet
from PIL import Image

from grafica.ui import load_firacode, ui_overlay


# Parametros del ciclo (minutos)
WORK_MINUTES = 25
REST_MINUTES = 5

# Colores (RGBA 0-255)
COLOR_WORK = (220, 130, 110, 255)   # tono calido (periodo de trabajo)
COLOR_REST = (130, 180, 220, 255)   # tono frio (descanso)
COLOR_TIME = (60, 40, 30, 255)      # texto del tiempo (marron oscuro)
COLOR_LABEL = (60, 40, 30, 255)     # texto WORK/REST
COLOR_PROGRESS = (180, 80, 60, 255) # barra de progreso (periodo actual)


class Pomodoro:
    """Timer visual Pomodoro. Se posiciona en la esquina superior izquierda."""

    # Estados
    STATE_WORK = "WORK"
    STATE_REST = "REST"

    def __init__(self, image_path, center_x, center_y, diameter=140):
        """Carga la imagen del loto y prepara el HUD.

        Args:
            image_path: ruta al PNG/WEBP circular del loto.
            center_x, center_y: centro del loto en pixeles de pantalla.
            diameter: diametro del loto en pixeles.
        """
        load_firacode()

        self.center_x = center_x
        self.center_y = center_y
        self.radius = diameter // 2

        # Estado del timer
        self.state = self.STATE_WORK
        self.time_left = WORK_MINUTES * 60.0  # segundos restantes
        self.total_time = WORK_MINUTES * 60.0
        self.running = True

        # Cargar imagen como textura
        self._load_texture(image_path, diameter)

        # Label superior (WORK / REST)
        self._label_state = pyglet.text.Label(
            self.state,
            font_name="Fira Code",
            font_size=11,
            x=center_x,
            y=center_y + self.radius - 18,
            anchor_x="center",
            anchor_y="center",
            color=COLOR_LABEL,
        )
        self._label_state_shadows = self._make_shadows(
            self._label_state, font_size=11, shadow_color=(255, 255, 255, 180),
        )

        # Label central: mm:ss
        self._label_time = pyglet.text.Label(
            self._format_time(self.time_left),
            font_name="Fira Code",
            font_size=22,
            x=center_x,
            y=center_y - 4,
            anchor_x="center",
            anchor_y="center",
            color=COLOR_TIME,
        )
        self._label_time_shadows = self._make_shadows(
            self._label_time, font_size=22, shadow_color=(255, 255, 255, 160),
        )

        # Label inferior: estado (corriendo / pausa)
        self._label_status = pyglet.text.Label(
            "",
            font_name="Fira Code",
            font_size=8,
            x=center_x,
            y=center_y - self.radius + 14,
            anchor_x="center",
            anchor_y="center",
            color=COLOR_LABEL,
        )
        self._label_status_shadows = self._make_shadows(
            self._label_status, font_size=8, shadow_color=(255, 255, 255, 150),
        )

        # Barra de progreso circular (arco) como shape
        self._progress_arc = pyglet.shapes.Arc(
            x=center_x,
            y=center_y,
            radius=self.radius - 6,
            start_angle=0,
            angle=0,  # se actualiza en refresh_progress
            color=COLOR_PROGRESS,
            thickness=4,
        )

        # Sprite del loto
        self._sprite = pyglet.sprite.Sprite(self._texture, x=center_x - self.radius, y=center_y - self.radius)

    def _make_shadows(self, base_label, font_size, shadow_color):
        """Crea 4 copias offset del label para simular un borde blanco."""
        offsets = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        shadows = []
        for dx, dy in offsets:
            shadows.append(pyglet.text.Label(
                base_label.text,
                font_name="Fira Code",
                font_size=font_size,
                x=base_label.x + dx,
                y=base_label.y + dy,
                anchor_x="center",
                anchor_y="center",
                color=shadow_color,
            ))
        return shadows

    def _load_texture(self, image_path, diameter):
        """Convierte el WEBP a una textura de pyglet con tamano cuadrado."""
        img = Image.open(image_path)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        # Reescalar al diametro deseado
        img = img.resize((diameter, diameter), Image.LANCZOS)
        # Pyglet acepta Image via texture_from_image
        self._texture = pyglet.image.ImageData(
            width=img.width,
            height=img.height,
            fmt="RGBA",
            data=img.tobytes(),
        )

    def _format_time(self, seconds):
        """Formatea segundos como mm:ss."""
        seconds = max(0, int(seconds))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def toggle_pause(self):
        """Pausa o reanuda el timer."""
        self.running = not self.running
        return self.running

    def skip_period(self):
        """Salta al siguiente periodo (work <-> rest)."""
        if self.state == self.STATE_WORK:
            self._switch_to(self.STATE_REST)
        else:
            self._switch_to(self.STATE_WORK)

    def reset(self):
        """Reinicia el periodo actual al inicio."""
        if self.state == self.STATE_WORK:
            self.time_left = WORK_MINUTES * 60.0
            self.total_time = WORK_MINUTES * 60.0
        else:
            self.time_left = REST_MINUTES * 60.0
            self.total_time = REST_MINUTES * 60.0
        self.running = True

    def _switch_to(self, new_state):
        """Cambia al estado dado y reinicia el tiempo."""
        self.state = new_state
        if new_state == self.STATE_WORK:
            self.time_left = WORK_MINUTES * 60.0
            self.total_time = WORK_MINUTES * 60.0
        else:
            self.time_left = REST_MINUTES * 60.0
            self.total_time = REST_MINUTES * 60.0
        self.running = True

    def update(self, dt):
        """Avanza el timer (llamar cada frame)."""
        if not self.running:
            return
        self.time_left -= dt
        if self.time_left <= 0:
            # Cambio automatico de periodo al llegar a 0
            if self.state == self.STATE_WORK:
                self._switch_to(self.STATE_REST)
            else:
                self._switch_to(self.STATE_WORK)

    def _refresh_labels(self):
        """Actualiza el texto de los labels y sus sombras."""
        self._label_state.text = self.state
        self._label_time.text = self._format_time(self.time_left)
        if self.running:
            self._label_status.text = "running"
        else:
            self._label_status.text = "paused (P)"
        for s in self._label_state_shadows:
            s.text = self._label_state.text
        for s in self._label_time_shadows:
            s.text = self._label_time.text
        for s in self._label_status_shadows:
            s.text = self._label_status.text

    def _refresh_progress(self):
        """Actualiza el arco de progreso (de 0 a 360 grados)."""
        if self.total_time <= 0:
            return
        fraction = max(0.0, min(1.0, 1.0 - self.time_left / self.total_time))
        # angle es el angulo total del arco (0 = invisible, 360 = circulo completo)
        self._progress_arc.angle = 360.0 * fraction
        self._progress_arc.visible = fraction > 0.001

    def _refresh_colors(self):
        """Cambia el color del progreso segun el estado."""
        if self.state == self.STATE_WORK:
            self._progress_arc.color = COLOR_WORK
            self._label_state.color = COLOR_WORK
        else:
            self._progress_arc.color = COLOR_REST
            self._label_state.color = COLOR_REST

    def draw(self):
        """Dibuja el Pomodoro encima de la escena 3D."""
        self._refresh_labels()
        self._refresh_progress()
        self._refresh_colors()
        with ui_overlay():
            self._sprite.draw()
            self._progress_arc.draw()
            # Sombras (borde blanco) detras del texto
            for s in self._label_state_shadows:
                s.draw()
            for s in self._label_time_shadows:
                s.draw()
            for s in self._label_status_shadows:
                s.draw()
            # Texto principal encima
            self._label_state.draw()
            self._label_time.draw()
            self._label_status.draw()
