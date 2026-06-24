# Issues — Escena Zuko vs. Ozai

## Task 2 — `21004082-K/test_shader.py`

### Resultado

- Archivo creado: `21004082-K/test_shader.py`
- Comando de verificación:
  ```bash
  PYTHONPATH=. SDL_VIDEODRIVER=dummy uv run python 21004082-K/test_shader.py 2>&1 | head -30
  ```
- Salida (sin errores, render + auto-close OK):
  ```
  Aplicando color forzado al modelo: [200 100  50 255]
  OK
  ```

### Notas técnicas / workarounds

- **Mismatch `vec3 color` vs `c4B` del `.off`**: el vertex shader declara
  `in vec3 color` (3 floats por vértice) pero `assets/cube.off` carga con
  `c4B/static` (4 bytes por vértice) y el helper `force_color` de
  `grafica.scenegraph_nodes` siempre rellena un buffer de 4 componentes.
  Al subir el buffer con `getattr(mesh_gpu, "color")[:] = data` falla con
  `ValueError: Can only assign sequence of same size`.
  - Workaround (sin tocar `grafica/`): después de `load_and_register_mesh`
    se reescribe `graph.meshes["cube"]["children"][0]["attributes"]["color"]`
    a 3 componentes con el color forzado. Sólo se hace para que el tamaño
    del buffer coincida con lo que el shader espera. El color visible sigue
    siendo el naranja pedido (RGB, no A — el fragment shader no usa alpha).
  - Este es un bug del helper, no del shader. Si en tareas siguientes se
    quiere usar alpha, hay que tocar el shader o el loader.

- **Uniforms de struct-arrays (PointLight / SpotLight)**: `set_global_attributes`
  falla con `ShaderException` al pasar arrays de structs porque pyglet
  strippea el `[0]` en introspección y la ruta `pipeline[attr] = value`
  no puede resolver nombres calificados. Se sube cada field por
  separado directamente sobre el pipeline:
  - `pipeline["pointLights[0].position"] = ...`, etc.
  - `pipeline["spotLights[0].position"] = ...`, etc.
  - `pipeline["material.ambient"] = ...`, etc.
- `view`, `projection`, `view_position` y `transform` sí funcionan vía
  `set_global_attributes` y `transform_parameter_name = "transform"`.

- **Cierre automático**: `pyglet.clock.schedule_interval(_close_after, 2.0)`.
  Imprime `OK` y cierra la ventana. Si el render lanza `ShaderException`,
  el `try/except` dentro de `on_draw` la captura, imprime el error y
  también cierra.

### Pendiente para los próximos tasks

- El bug del `force_color` con `vec3 color` se repite cada vez que se
  intente usar el helper con este shader; mientras no se arregle el
  loader o se cambie el shader a `vec4`, hay que patchear a mano el
  atributo después de cada `load_and_register_mesh`.
- Cuando se agreguen más mallas habrá que reproducir el mismo workaround.
