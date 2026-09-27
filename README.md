# Aang meditando con ambiente Lo-Fi

Este proyecto fue desarrollado como parte del ramo **Modelación y Computación Gráfica para Ingenieros** (CC3501) de la Universidad de Chile.

Este proyecto es una escena interactiva 3D creada en Python usando `pyglet` y OpenGL. Muestra al personaje Aang meditando en posición de loto, con un ciclo dinámico de día y noche.

## Características

* **Animación y Skinning 3D**: Animación de respiración y viento aplicadas al esqueleto de Aang.
* **Ciclo de Día y Noche**: Iluminación dinámica y _skybox_ que cambia progresivamente con el tiempo.
* **Cámara Orbital**: Control interactivo con mouse y teclado.
* **Temporizador Pomodoro**: Integrado en la interfaz con un ícono temático.
* **Reproductor Lo-Fi**: Música de fondo ambiental interactiva.

## Requisitos y Ejecución

El proyecto utiliza `uv` como administrador de entornos.

Para ejecutar la escena, debes correr el siguiente comando:

```bash
uv run python -m 21004082-K
```

## Controles

* **A/D o ←/→** : Orbitar
* **Mouse** : Girar vista
* **Rueda** : Zoom
* **R** : Reset de cámara
* **ESPACIO** : Pausar/Reanudar ciclo temporal
* **M** : Activar/Desactivar audio Lo-Fi
* **P** : Pausar/Reanudar Pomodoro
* **N** : Siguiente ciclo de Pomodoro
* **ESC** : Salir
