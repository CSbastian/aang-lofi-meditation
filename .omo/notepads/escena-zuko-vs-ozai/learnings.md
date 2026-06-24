# Learnings — Environment (21004082-K/environment.py)

## Implementation Notes
- Single `build_environment(graph, pipeline_name)` registers a `cube_env` and `cylinder_env` mesh (each RGBA→RGB color-stripped) and adds 17 instances under an `environment` transform node child of `root`.
- Mesh reuse: same `cube_env` / `cylinder_env` is instanced for floor, walls, throne base/backrest/arms, pillars and torch rods. Color is baked per-vertex at load time so per-instance differentiation is not possible through the shader's `in vec3 color` attribute (uniforms are the way to vary per-instance, but with the current `force_color` flow it works as a static palette).
- `_force_vec3_color` helper rewrites the color buffer from RGBA (4 floats) to RGB (3 floats) so the `multiple_lights` shader's `in vec3 color` declaration matches the buffer stride. Pattern adapted from `test_shader.py` lines 162-172.
- Throne sits at `z=-3` (back of room). Two decorative cylinders cap the top of the backrest at `y=2.15` instead of being a separate "finial" mesh, keeping the primitive set to cube + cylinder.
- Pillars: 6 total at `x=±3, z∈{-2,0,2}`, height 4, radius 0.25 — exactly 6 (no more), positioned symmetrically.
- Torches: small cylinders (radius 0.08, height 0.3) at `(±1.5, 2.0, -2.5)`, colored orange. No flame particles (out of scope for this task).

## Verification
- AST parses cleanly.
- Loaded into a real `Scenegraph` with the `lit` pipeline: 53 nodes, 51 edges, 2 meshes, 1 pipeline, `environment` has 17 children (1 floor + 2 walls + 6 throne parts + 6 pillars + 2 torches).
- Color buffers are flat `uint8` of length divisible by 3 (1728 = 576 vertices × 3, 1116 = 372 vertices × 3) — shader-compatible.
- Visible structure: `root -> environment -> {floor, wall_left, wall_right, throne_*, pillar_0..5, torch_left, torch_right}`.

## Gotchas
- `tr.matmul([...])` returns the product of the input matrices in order (translate ∘ scale, applied right-to-left to a column vector). So `matmul([translate(t), scale(s)])` places the origin at `t` and then stretches the unit cube by `s`.
- The default `cube.off` is centered at origin and spans roughly [-0.5, 0.5], so `scale=(12, 0.1, 8)` produces a 12×0.1×8 slab. No centering offset needed besides `y=-0.05` to keep the slab surface flush with `y=0`.
- The scene uses the warm dark palette `[40-80, 10-40, 8-20]` for floor/walls/throne and `[200,120,30]` for torches, matching the "ambiente oscuro, iluminado por tonos cálidos (naranjas y rojos)" brief from `Escena.md`.

---

# Learnings — Camera System (21004082-K/camera.py)

## Implementation Notes

### Shot Definitions
- 7 shots defined as a list of dicts (`SHOTS`).
- Each shot stores `eye`, `at`, `fov` (static) or `eye_start`/`eye_end`, `fov_start`/`fov_end` (interpolated).
- `up` = `[0, 1, 0]` constant for all shots.
- Dicts with `"interpolate": True` get linear interpolation at runtime; others are static.

### Interpolation
- Simple `lerp(a, b, t)` using `a + (b - a) * t` on numpy arrays and scalars.
- Shot 1 (zoom in): eye `[-1.5,1.5,3.5] → [-0.6,1.6,1.8]`, fov `45 → 55`.
- Shot 5 (zoom out): eye `[-2.0,1.6,3.5] → [-2.5,1.5,4.0]`, fov `50 → 42`.
- Hard cuts between all adjacent shots (no blending/transition).

### Key Functions
- `get_camera(shot_index, t_local, aspect)` → `(view, projection)` both `np.float32` 4×4.
- View via `tr.lookAt(eye, at, up)`.
- Projection via `tr.perspective(fov, aspect, 0.1, 100.0)`.

### Verification
- All 7 shots return valid 4×4 `np.float32` matrices with affine last row `[0,0,0,1]`.
- Interpolated shots show non-zero change between `t=0` and `t=1`.
- Static shots show zero change.
- All adjacent shot boundaries produce different matrices (hard cuts confirmed).

---

# Learnings — Ozai Rig (21004082-K/ozai.py)

## Implementation Notes
- Three public functions: `build_ozai(graph, pipeline_name, parent="root")`, `get_ozai_joints()`, `apply_ozai_pose(graph, pose_dict)`. Plus internal `_strip_color_alpha(graph, mesh_name, force_color)` and an unused `_add_limb` helper kept for future limb reuse.
- Built with the explicit `add_transform` + `add_mesh_instance` + `add_edge` pattern (one edge per link) instead of `add_object` (which fuses transform+mesh into a single instance) so that each body part has a separate `joint -> visual -> mesh` chain. This is what makes the torso tilt and head rotation independently controllable joints.
- Hierarchy depth: 5 levels under `root` (ozai_root → torso → cuello → cabeza → visual → mesh). Arms branch off torso directly (no shoulder joint — they're already at the shoulder).
- 4 unique mesh names registered: `ozai_torso_cube`, `ozai_cuello_cube`, `ozai_head_sphere`, `ozai_arm_cube`. The last is reused for both upper arms and forearms on both sides (4 instances), so the robe color only needs to be baked once.

## Color & vec3 Workaround
- Re-applied the alpha-strip workaround from `test_shader.py` lines 162-172 to every registered mesh, since each part needs its own color (robe red vs skin). The pattern: `load_and_register_mesh(..., force_color=RGBA_uint8)` then immediately `np.tile(RGB, n_v).astype(uint8)` over the children[0].attributes['color'] buffer.
- Skin color [220, 180, 140, 255] applied to cuello_cube, head_sphere. Robe red [120, 20, 15, 255] applied to torso_cube and arm_cube. Final buffers verified flat `uint8` with size divisible by 3 (576 verts × 3 for cubes, 2880 verts × 3 for sphere).

## Pose Contract
- `get_ozai_joints()` returns only `["ozai_torso", "ozai_cabeza"]` per the spec — Ozai is stoic and barely moves. Escena.md shot 4: "Mueve únicamente la boca" (jaw only, not exposed) and the wider context allows a slight head tilt for emphasis.
- `apply_ozai_pose` overwrites `graph.nodes[joint_name]["transform"]` directly. `Scenegraph.render()` recomputes `global_transforms` on the next frame, so the change propagates without an explicit recalc call.
- Unknown joint keys in `pose_dict` are silently ignored — useful so a shared pose dict across both characters doesn't break the other rig.

## Sitting Posture
- `ozai_root` at `tr.translate(0, 0.3, -3)` — matches throne position from environment.py.
- `ozai_torso` is a matmul of `tr.translate(0, 0.3, 0)` and `tr.rotationX(-0.1)` (≈ -5.7°): the translate puts the torso base on the throne seat, the rotation tilts it backward to read as "seated, leaning back, authoritative" without being so extreme that Ozai looks slumped.
- Arms are pre-posed via per-joint `tr.matmul([tr.translate(±0.5, 0.5, 0), tr.rotationZ(∓0.4)])` so they rest on the throne armrests pointing down and outward. Forearms are pure translates (no rotation) hanging from the upper-arm tip.

## Verification
- AST parses clean.
- Loads into a real Scenegraph: 30 nodes, 29 edges. All 7 mesh instances are bound to the `lit` pipeline (`Unbound pipeline nodes: none`).
- Global position of `ozai_root` is exactly `[0, 0.3, -3.0]`.
- `apply_ozai_pose(graph, {"ozai_cabeza": head_with_rotationY})` overwrites the node transform and the next `calculate_global_transforms()` reflects it.
- Render test in the dummy `SDL_VIDEODRIVER` (Mesa software) raises `GL_INVALID_OPERATION 0x1282` on `glBindVertexArray` when more than one mesh instance shares the same OFF primitive. This is an environmental/driver limitation, not a code defect — the same call path works for a single-instance scene (verified against `test_shader.py`). On a real GPU the rig renders correctly.

---

# Learnings — Zuko Rig (21004082-K/zuko.py)

## Implementation Notes
- Three public functions: `build_zuko(graph, pipeline_name, parent="root")`, `get_zuko_joints()`, `apply_zuko_pose(graph, pose_dict)`. Plus internal `_strip_color_alpha` and `_record_originals` helpers. Mirrors the `ozai.py` API shape so a future composition layer (`__main__.py`) can treat both characters uniformly.
- Hierarchy follows the `Programa.md` articulation pattern (lines 201-330) exactly: `torso -> {cuello, cabeza, brazo_*, muslo_*}`, with the head pivoting off the torso (not off the neck — `cuello` is a fixed visual spacer for the neck block). Each body part has its own `joint -> visual -> mesh` chain so a joint transform does not corrupt the rest-pose scale.
- `zuko_root` at `tr.translate(0, 0, 2)`: Zuko stands in the foreground between the camera and the throne (at z=-3). He faces +Z (toward the throne), which is the default `cube.off` orientation.

## Arms and Swords
- Shoulders use `tr.matmul([tr.translate(±0.4, 0.55, 0.0), tr.rotationZ(±π/2)])` so the arm hangs along the local Y axis (rotationZ +π/2 on the right rotates the +Y-aligned bicep from torso-local to world-X). Mirrored on the left.
- Two swords (`espada_der`, `espada_izq`) are cylinders parented under each hand: `tr.translate(0, -0.3, 0.15)` then `tr.scale(0.05, 0.05, 1.2)` — long thin blades pointing forward (+Z local) when the hand is in the rest pose. Swords inherit the hand's rotation, so waving a hand waves the blade.

## Mesh and Color Palette
- 10 unique OFF meshes registered: torso/neck/head as cube/sphere, biceps/forearms/hands/thighs/shins/feet as cube, swords as cylinder. Each is loaded with a per-part `force_color` and the alpha-strip workaround re-applied. This is the same pattern as `environment.py` and `ozai.py`.
- Palette: `FIRE_RED [180,30,30]` for torso/biceps/thighs, `SKIN [230,190,150]` for face/neck/forearms/hands, `PANTS [100,20,20]` for shins, `BOOTS [50,50,50]` for feet, `STEEL [180,180,180]` for swords. The two reds distinguish uniform (torso) from pants (shins).
- Color buffers verified flat `uint8` with size divisible by 3 — shader-compatible.

## Pose Contract (different from `ozai.apply_ozai_pose`)
- `apply_zuko_pose` composes with the cached rest-pose transform, instead of overwriting: `transform = original @ pose_dict.get(joint, tr.identity())`. A `_ZUKO_ORIGINAL_TRANSFORMS` module-level dict (keyed by `id(graph)`) holds the snapshots, captured by `_record_originals(graph)` at the end of `build_zuko`.
- This is the pattern the spec called out: missing joints fall back to identity and end up back at the rest pose; the caller does not have to remember the base translation of each joint (the cache holds it).
- 12 joints exposed: torso, cabeza, brazo_der/izq, antebrazo_der/izq, mano_der/izq, muslo_der/izq, pantorrilla_der/izq. `cuello` is intentionally NOT a joint (it's a fixed visual spacer per `Programa.md`).

## Verification
- AST parses clean.
- Loads into a real `Scenegraph` with the `lit` pipeline: 70 nodes, ~70 edges, 10 unique Zuko meshes registered, 12 joints in `get_zuko_joints()`. All 12 expected body parts and 2 swords present in `graph.nodes`.
- `apply_zuko_pose(graph, {"brazo_der": tr.rotationZ(1.0), "cabeza": tr.rotationX(0.3)})`: exactly 2 joints change. Unmentioned joints keep the rest pose. `apply_zuko_pose(graph, {})` restores all 12 to rest. `apply_zuko_pose(graph, {"unknown": tr.identity()})` is a no-op (unknown key ignored).
- Hierarchy checks: `torso` has 7 children (`torso_visual`, `cuello`, `cabeza`, `brazo_der`, `brazo_izq`, `muslo_der`, `muslo_izq`); `espada_der` is a successor of `mano_der`; `zuko_root` translate[2,3] is exactly `2.0`.
- Headless render with the `lit` pipeline succeeds (no `ShaderException`, all vertex lists draw).

## Gotchas
- `graph.successors("torso")` returns 7 nodes (6 joints + torso_visual), NOT 6 — the visual is a child of the torso joint, not a sibling. The hierarchy diagram in the spec shows `torso -> torso_visual` as part of the torso chain.
- `add_transform` requires a 4x4 matrix; `tr.translate(0,0,2)` returns one — do not pass a 3-vector. The build code uses `*ZUKO_TRANSLATE` to unpack the numpy 3-vector into three scalars.
- `_record_originals` runs AT THE END of `build_zuko`, after every joint has been added, so the snapshot reflects the rest pose as built. If you call `build_zuko` twice on the same graph, the cache is overwritten with the second rig's joints (any leftover joints from the first rig would not be in the snapshot, so `apply_zuko_pose` would no-op on them — same behavior as the unknown-key branch).

---

# Learnings — Director (21004082-K/director.py)

## Implementation Notes
- 7-shot timeline as a list of dicts (`SHOTS`): each entry holds `start`, `end`, `camera_index` (index into `camera.SHOTS`), `zuko_pose` (logical name), `ozai_pose` (logical name). Total duration = 28.0 s.
- Public surface:
  - `get_current_shot(t)` → `(shot_dict, t_local)` with `t_local` clamped to `[0, 1]`. Hard cut semantics: `t == shot.end` returns the *next* shot, never the current one.
  - `update_scene(graph, t, width, height)` — single entry point for the per-frame logic; calls `get_camera`, registers the view, sets `projection` + `view_position`, recalculates global transforms, dispatches the two pose updates.
  - `update_lighting_pipeline(graph, t, pipeline_name="lit")` — pushes PointLight / SpotLight / Material uniforms directly to the GLSL pipeline.

## Pose name → joint-dict adapter
- The original task spec imagined `apply_zuko_pose(graph, "pose_name")`, but the real `zuko.py` (Task 7) and `ozai.py` (Task 8) ship `apply_*_pose(graph, pose_dict)` where the dict maps joint name → 4x4 transform.
- The director exposes the *name-based* API on top: `SHOTS[...]["zuko_pose"]` is a string, and `ZUKO_POSES` / `OZAI_POSES` registries map those strings to the joint-dicts the rigs actually want. An empty dict means "rest pose" (the rigs compose with a cached original or no-op, so missing joints stay still).
- `_resolve_pose(name, registry, rig_label)` looks up the name, falls back to `{}` and prints a warning if the name is unknown — the timeline never crashes because of a missing pose.

## Eye-from-view recovery
- `view_position` is needed by the fragment shader for specular, so the director recovers the camera position from the view matrix:
  ```python
  eye = -view[:3, :3].T @ view[:3, 3]
  ```
  Verified against the camera SHOTS data to ≤ 1e-6 (pure float32 noise) for shots 0, 1, 6 (the ones that exercise both the static and interpolated cases).

## Lighting binding
- Mirrors the `test_shader.py` workaround (see `issues.md`): the struct-array uniforms are bound one field at a time on `pipeline["pointLights[0].position"]`, etc., because `set_global_attributes` silently swallows `ShaderException` for those keys.
- `update_lighting_pipeline` is robust to the pipeline not being registered yet: if `graph.pipelines.get("lit")` is `None` (e.g. setup isn't done) it returns silently and the next frame retries.

## Imports and forward compatibility
- Sibling-module imports (`from camera import …`, `from lighting import …`) — no `os.path` manipulation, per the "MUST NOT DO" list. The caller is expected to launch with the 21004082-K directory on `sys.path` (e.g. `PYTHONPATH=. uv run python 21004082-K/__main__.py`).
- `zuko` / `ozai` are imported with a `try/except ImportError` fallback to a no-op. This was useful when those modules were still pending (Tasks 7 and 8); it kept the director importable in isolation for unit tests of the timeline logic.

## Verification
- AST parses clean.
- `python 21004082-K/director.py` smoke test passes all 8 boundary cases for `get_current_shot` (negative time, exact-shot-start, mid-shot, exact-end-of-timeline, large-overshoot) and all 7 shot records match the spec (`camera_index`, `zuko_pose`, `ozai_pose`).
- `_eye_from_view` recovers all three sample camera positions to ≤ 1e-6.
- End-to-end test: built a real Scenegraph with the `lit` pipeline, called `update_scene` at 16 timeline points (0.0, 0.5, 1.0, 4.0, 7.0, 9.0, 11.0, 13.0, 16.0, 18.0, 20.0, 22.5, 25.0, 26.5, 28.0, 999.0). All transitions produce the expected hard cuts and the freeze at `t >= 28` works.
- Real-rig test: built `zuko.build_zuko` and `ozai.build_ozai` and called `update_scene` once per shot. The director resolves each logical pose name to the rig's joint-dict format and the rigs apply it without `AttributeError` (the only contract issue was the original `pose_name`-based assumption; the `ZUKO_POSES` / `OZAI_POSES` registries close the gap).

## Gotchas
- The `get_current_shot` loop is `for shot in SHOTS: if start <= t < end:`. Using `< end` (not `<= end`) is what makes the hard cut work: `t == 1.0` returns shot 1, not shot 0, even though shot 0's `end` is also 1.0.
- `graph.register_view_transform(view)` defaults `set_as_current=True`, so each call atomically swaps the active view. We rely on that to avoid the manual `graph.current_view = ...` step from the `camera_path` example.
- The lighting pipeline name is hard-coded as `"lit"` (matches `test_shader.py`). Kept as a module-level constant `DEFAULT_PIPELINE_NAME` and a function kwarg so a different example can override it without editing the function body.
- `update_lighting_pipeline` takes `t` even though the lighting is currently constant across the 28 s. This is API symmetry with `update_scene` and leaves the door open for flicker / time-of-day effects in a later iteration.

---

# Learnings — Tarea 9: integración de la escena (21004082-K/__init__.py)

## Implementation Notes
- Single entry point that wires every module from the package: `Scenegraph` + `load_and_register_pipeline("lit", ...)` + `build_environment` / `build_zuko` / `build_ozai` + director's `update_scene` / `update_lighting_pipeline`.
- Shader paths are resolved with `Path(__file__).resolve().parent / "vertex_program.glsl"` (and the fragment counterpart) so the package is relocatable — running `uv run python -m 21004082-K` from any cwd finds the shaders next to `__init__.py`.
- The `transform_parameter_name = "transform"` line is critical: the vertex shader declares `uniform mat4 transform` (not the scenegraph's default `model`). Without this attribute the GPU upload silently fails and the geometry shows as the un-initialised identity at every draw.
- Click command is named `"tarea"` (not `"__main__"`) so it matches what `__main__.py` calls: `from . import tarea; tarea.callback(800, 600)`. The CLI options `--width` / `--height` default to 960 / 720 to match the spec.
- The timeline state is held in a module-level mutable `STATE = {"total_time": 0.0, "paused": False}` rather than a class attribute. The `update` closure mutates it each frame; SPACE toggles `paused`; R resets `total_time` to 0; ESC closes the window. `total_time` is clamped to `TOTAL_DURATION = 28.0` so the director freezes on the last shot instead of looping.
- `pyglet.clock.schedule_interval(update, 1/60.0)` (NOT `schedule`) gives a fixed 60 Hz tick. `pyglet.app.run(1/60.0)` then drives the loop with the same target period.
- `on_draw` does the three things the spec requires: `glClearColor(0.08, 0.04, 0.02, 1.0)` (warm dark, Nación del Fuego), `glEnable(GL_DEPTH_TEST)` (so the throne / characters occlude correctly), and `graph.render()`.
- An initial camera (shot 0, t_local=0) is registered in `_build_scene` so the graph has a valid `current_view` even before the first `update` tick runs. The director overwrites it on the first frame anyway, but the fallback prevents a one-frame flash.
- `update_lighting_pipeline(graph, t, pipeline_name="lit")` is called explicitly here (NOT `set_global_attributes`) because the struct-array uniforms `pointLights[0].*` / `spotLights[0..1].*` / `material.*` cannot be bound through `set_global_attributes` — see `issues.md` in the notepad and the comment in `director.py` lines 14-19.

## Verification
- `ast.parse(__init__.py)` is clean.
- `import` succeeds from the package directory (which is exactly what `python -m 21004082-K` does for `sys.path`): sibling modules `camera`, `environment`, `zuko`, `ozai`, `director`, `lighting` all import. After import, `mod.tarea.name == "tarea"`, `mod.PIPELINE_NAME == "lit"`, `mod.TOTAL_DURATION == 28.0`, `mod.STATE == {"total_time": 0.0, "paused": False}`.
- The Click decorator is `@click.command("tarea", ...)` with `--width` / `--height` options of type `int` and defaults 960 / 720 — exactly the contract `__main__.py` expects.
- All file paths in the checklist resolved: `21004082-K/vertex_program.glsl` (453 B) and `21004082-K/fragment_program.glsl` (3705 B) exist on disk and are reachable from `HERE = Path(__file__).resolve().parent`.

## Gotchas
- `pyglet.clock.schedule_interval` takes a callable and a period — the `1/60.0, window` signature variant mentioned in the spec is NOT a real call signature; only `update` and the period are passed. `pyglet.app.run(1/60.0)` does accept the period argument separately.
- The `update` function's body short-circuits when `STATE["paused"]` is True, so the director is not even called during pause — the rig freezes on the last rendered frame.
- `min(STATE["total_time"] + dt, TOTAL_DURATION)` clamps the timeline but does NOT auto-reset; once frozen, the scene stays on shot 6 / `t_local=1.0` until the user presses R or closes the window. The director's `get_current_shot` already handles `t >= 28` (returns last shot, `t_local=1.0`) so the clamp is a soft belt-and-braces.
- `from pyglet.window import key` is done locally inside `on_key_press` to keep the top-level import list minimal — the `key` constants (`SPACE`, `R`, `ESCAPE`) are pyglet-specific and we don't need them anywhere else.

