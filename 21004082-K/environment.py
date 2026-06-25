"""Sala del trono de la Nación del Fuego.

Construye el entorno estático (piso, paredes, trono, pilares y antorchas)
a partir de las primitivas básicas de ``assets/`` (cube, sphere, cylinder).

Todas las mallas se registran con ``force_color`` y, dado que el shader de
iluminación (``multiple_lights``) declara ``in vec3 color`` mientras que
``.off`` entrega RGBA, se reescribe el buffer de color a 3 componentes
después de ``load_and_register_mesh``. Ver ``21004082-K/test_shader.py``
para el patrón de workaround.
"""

from pathlib import Path

import numpy as np

import grafica.transformations as tr
from grafica.scenegraph import Scenegraph


# Rutas a las primitivas base del repositorio.
REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
CUBE_PATH = ASSETS_DIR / "cube.off"
CYLINDER_PATH = ASSETS_DIR / "cylinder.off"

# Paleta de la Nación del Fuego (RGBA, uint8).
COLOR_FLOOR = np.array([60, 15, 10, 255], dtype=np.uint8)
COLOR_WALL = np.array([40, 10, 8, 255], dtype=np.uint8)
COLOR_THRONE = np.array([80, 40, 20, 255], dtype=np.uint8)
COLOR_PILLAR = np.array([50, 40, 35, 255], dtype=np.uint8)
COLOR_TORCH = np.array([200, 120, 30, 255], dtype=np.uint8)


def _force_vec3_color(graph: Scenegraph, mesh_name: str, force_color: np.ndarray) -> None:
    """No-op: el shader ahora acepta ``in vec4 color`` (4 componentes).

    El loader de ``.off`` produce un color RGBA (4 componentes por vértice)
    que coincide con el shader adaptado. Esta función se mantiene como
    stub por compatibilidad pero ya no modifica el buffer.
    """
    pass


def _add_env_object(
    graph: Scenegraph,
    name: str,
    mesh_name: str,
    pipeline_name: str,
    parent: str,
    translation: tuple,
    scale: tuple,
) -> None:
    """Atajo: registra una instancia bajo ``parent`` con translate ∘ scale."""
    transform = tr.matmul(
        [tr.translate(*translation), tr.scale(*scale)]
    )
    graph.add_object(
        name,
        mesh_name,
        pipeline_name,
        parent=parent,
        transform=transform,
    )


def build_environment(graph: Scenegraph, pipeline_name: str) -> None:
    """Agrega la sala del trono al grafo de escena bajo ``environment``.

    Estructura:
        root -> environment -> {floor, walls, throne_parts, pillars, torches}

    Las mallas ``cube_env`` y ``cylinder_env`` se registran una sola vez y
    luego se referencian desde cada instancia; el shader trata cada
    instancia de forma independiente porque el color se fija por vértice
    en la carga.
    """

    # -------------------------------------------------------------- #
    # 1. Mallas compartidas
    # -------------------------------------------------------------- #
    graph.load_and_register_mesh(
        "cube_env", str(CUBE_PATH), force_color=COLOR_FLOOR.copy()
    )
    _force_vec3_color(graph, "cube_env", COLOR_FLOOR)

    graph.load_and_register_mesh(
        "cylinder_env", str(CYLINDER_PATH), force_color=COLOR_PILLAR.copy()
    )
    _force_vec3_color(graph, "cylinder_env", COLOR_PILLAR)

    # -------------------------------------------------------------- #
    # 2. Nodo transform "environment" (padre de todos los componentes)
    # -------------------------------------------------------------- #
    graph.add_transform("environment", tr.identity())
    graph.add_edge(graph.root_key, "environment")

    # -------------------------------------------------------------- #
    # 3. Piso
    # -------------------------------------------------------------- #
    _add_env_object(
        graph,
        "floor",
        "cube_env",
        pipeline_name,
        parent="environment",
        translation=(0.0, -0.05, 0.0),
        scale=(12.0, 0.1, 8.0),
    )

    # -------------------------------------------------------------- #
    # 4. Paredes (izquierda y derecha)
    # -------------------------------------------------------------- #
    _add_env_object(
        graph,
        "wall_left",
        "cube_env",
        pipeline_name,
        parent="environment",
        translation=(-6.0, 2.0, 0.0),
        scale=(0.2, 4.0, 8.0),
    )
    _add_env_object(
        graph,
        "wall_right",
        "cube_env",
        pipeline_name,
        parent="environment",
        translation=(6.0, 2.0, 0.0),
        scale=(0.2, 4.0, 8.0),
    )

    # -------------------------------------------------------------- #
    # 5. Trono (z = -3, fondo de la sala)
    # -------------------------------------------------------------- #
    # Base
    _add_env_object(
        graph,
        "throne_base",
        "cube_env",
        pipeline_name,
        parent="environment",
        translation=(0.0, 0.15, -3.0),
        scale=(2.0, 0.3, 1.5),
    )
    # Respaldo
    _add_env_object(
        graph,
        "throne_backrest",
        "cube_env",
        pipeline_name,
        parent="environment",
        translation=(0.0, 1.15, -3.9),
        scale=(2.0, 2.0, 0.3),
    )
    # Brazos
    _add_env_object(
        graph,
        "throne_arm_left",
        "cube_env",
        pipeline_name,
        parent="environment",
        translation=(-1.0, 0.45, -3.0),
        scale=(0.3, 0.6, 0.8),
    )
    _add_env_object(
        graph,
        "throne_arm_right",
        "cube_env",
        pipeline_name,
        parent="environment",
        translation=(1.0, 0.45, -3.0),
        scale=(0.3, 0.6, 0.8),
    )
    # Decoración: cilindros en los extremos del respaldo
    _add_env_object(
        graph,
        "throne_decor_left",
        "cylinder_env",
        pipeline_name,
        parent="environment",
        translation=(-0.95, 2.15, -3.9),
        scale=(0.12, 0.4, 0.12),
    )
    _add_env_object(
        graph,
        "throne_decor_right",
        "cylinder_env",
        pipeline_name,
        parent="environment",
        translation=(0.95, 2.15, -3.9),
        scale=(0.12, 0.4, 0.12),
    )

    # -------------------------------------------------------------- #
    # 6. Pilares (6) en x = ±3, z ∈ {-2, 0, 2}
    # -------------------------------------------------------------- #
    pillar_z = [-2.0, 0.0, 2.0]
    for x_sign in (-1.0, 1.0):
        for z in pillar_z:
            idx = (1 if x_sign > 0 else 0) * 3 + pillar_z.index(z)
            _add_env_object(
                graph,
                f"pillar_{idx}",
                "cylinder_env",
                pipeline_name,
                parent="environment",
                translation=(x_sign * 3.0, 2.0, z),
                scale=(0.25, 4.0, 0.25),
            )

    # -------------------------------------------------------------- #
    # 7. Antorchas (2) cerca del trono
    # -------------------------------------------------------------- #
    _add_env_object(
        graph,
        "torch_left",
        "cylinder_env",
        pipeline_name,
        parent="environment",
        translation=(-1.5, 2.0, -2.5),
        scale=(0.08, 0.3, 0.08),
    )
    _add_env_object(
        graph,
        "torch_right",
        "cylinder_env",
        pipeline_name,
        parent="environment",
        translation=(1.5, 2.0, -2.5),
        scale=(0.08, 0.3, 0.08),
    )
