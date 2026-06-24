# Assets — Escena Zuko vs Ozai

## Busqueda de modelos 3D

Se realizó una búsqueda de modelos 3D gratuitos para representar a los
personajes **Zuko** (guerrero ágil) y **Ozai** (rey/poderoso) usando
Sketchfab, CGTrader y otros repositorios de assets gratuitos.

### Resultados de la búsqueda

| Personaje | Fuente | Licencia | Problema |
|-----------|--------|----------|----------|
| Zuko | [Sketchfab - Chechorams16](https://sketchfab.com/3d-models/zuko-avatar-the-last-airbender-45ee31248ed94f6db1b42b563b79c358) | CC Attribution | Descarga requiere navegador interactivo; modelo único (no articulado) |
| Zuko | [CGTrader](https://www.cgtrader.com/free-3d-models/character/clothing/prince-zuko-from-avatar-the-last-airbender-plus-clothes-md) | Custom (no AI) | Licencia restrictiva; modelo único, no articulado |
| Ozai | — | — | **No se encontraron modelos gratuitos** para Ozai |
| Guerrero genérico | [Sketchfab - Nordener](https://sketchfab.com/3d-models/warrior-3dmodel-2f919b1722b44578a9c423cade9a6daf) | CC Attribution | ~300k triángulos, modelo único |

### Conclusión

No hay modelos gratuitos adecuados porque:

1. **Cuerpo articulado**: Necesitamos partes separadas (torso, cabeza,
   brazos, piernas) para animar articulaciones independientemente.
   Los modelos encontrados son mallas únicas no diseñadas para
   descomposición en partes.
2. **Descarga compleja**: Sketchfab requiere navegador interactivo
   para descargar; no es automatizable vía CLI.
3. **Ozai no disponible**: No se encontró ningún modelo gratuito de Ozai.

## Estrategia de respaldo: Primitivas del repositorio

Usaremos las primitivas OFF incluidas en `assets/` del repositorio
base, combinadas con colores forzados para la paleta de la Nación del
Fuego.

### Mapeo de partes del cuerpo

| Parte | Primitiva | Archivo | Color (Fire Nation) |
|-------|-----------|---------|---------------------|
| Torso | Cubo | `assets/cube.off` | Rojo oscuro `[180, 30, 30, 255]` |
| Cabeza | Esfera | `assets/sphere.off` | Piel `[230, 190, 150, 255]` |
| Brazos | Cilindros | `assets/cylinder.off` | Rojo oscuro `[180, 30, 30, 255]` |
| Piernas | Cilindros | `assets/cylinder.off` | Rojo oscuro `[180, 30, 30, 255]` |

### Uso en código

Las primitivas se cargan con `_node_from_file` usando `force_color`
para asignar colores RGBA sin necesidad de texturas:

```python
import numpy as np
from grafica.scenegraph_nodes import _node_from_file

torso = _node_from_file(
    "assets/cube.off",
    force_color=np.array([180, 30, 30, 255], dtype=np.uint8)
)
cabeza = _node_from_file(
    "assets/sphere.off",
    force_color=np.array([230, 190, 150, 255], dtype=np.uint8)
)
brazo = _node_from_file(
    "assets/cylinder.off",
    force_color=np.array([180, 30, 30, 255], dtype=np.uint8)
)
pierna = _node_from_file(
    "assets/cylinder.off",
    force_color=np.array([100, 20, 20, 255], dtype=np.uint8)
)
```

### Notas

- Las primitivas se escalan y transforman mediante matrices de
  transformación (escala, rotación, traslación) para formar la
  silueta de cada personaje.
- Cada personaje se estructura como un grafo de escena donde cada
  parte del cuerpo es un nodo hijo con su transformación local.
- Esto permite animar articulaciones (hombros, codos, caderas,
  rodillas) modificando las transformaciones locales de cada nodo.
- Los colores se definen por personaje: **Zuko** usa rojo Fire
  Nation con detalles dorados; **Ozai** usa rojo más oscuro y
  tonos imperiales.
