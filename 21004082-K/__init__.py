import click
import numpy as np
import pyglet
import pyglet.gl as GL
from pathlib import Path
from pyglet.gl import GLfloat

import grafica.transformations as tr
from grafica.ui import ui_overlay
from grafica.utils import load_pipeline


@click.command("tarea", short_help="Escena 3D: Aang meditando con ambiente Lo-Fi")
@click.option("--width", type=int, default=1024)
@click.option("--height", type=int, default=768)
def tarea(width, height):
    # ===== IMPORTS INSIDE TO AVOID CIRCULAR =====
    import importlib
    camera_mod = importlib.import_module("21004082-K.camera")
    scene_mod = importlib.import_module("21004082-K.scene_builder")
    aang_mod = importlib.import_module("21004082-K.aang")
    particles_mod = importlib.import_module("21004082-K.particles3d")
    audio_mod = importlib.import_module("21004082-K.audio")
    skybox_mod = importlib.import_module("21004082-K.skybox")

    LoFiCamera = camera_mod.LoFiCamera
    build_scene = scene_mod.build_scene
    get_lighting_config = scene_mod.get_lighting_config
    setup_lighting = scene_mod.setup_lighting
    setup_aang = aang_mod.setup_aang
    compute_skin_matrices = aang_mod.compute_skin_matrices
    apply_breathing_and_wind = aang_mod.apply_breathing_and_wind
    compute_aang_bbox = aang_mod.compute_aang_bbox
    apply_lotus_pose = aang_mod.apply_lotus_pose
    ParticleSystem3D = particles_mod.ParticleSystem3D
    setup_particle_renderer = particles_mod.setup_particle_renderer
    render_particles = particles_mod.render_particles
    load_lofi_audio = audio_mod.load_lofi_audio
    setup_skybox = skybox_mod.setup_skybox
    render_skybox = skybox_mod.render_skybox

    # ===== WINDOW SETUP =====
    window = pyglet.window.Window(width, height, caption="Aang Meditando — Lo-Fi")
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

    # ===== FONT =====
    pyglet.font.add_file(str(Path(__file__).parent.parent / "assets" / "FiraCode" / "FiraCode-Regular.ttf"))

    # ===== SHADERS =====
    shaders_dir = Path(__file__).parent / "shaders"
    phong_pipeline = load_pipeline(
        str(shaders_dir / "phong_vertex.glsl"),
        str(shaders_dir / "phong_fragment.glsl"),
    )
    skinning_pipeline = load_pipeline(
        str(shaders_dir / "skinning_lbs_vertex.glsl"),
        str(shaders_dir / "skinning_phong_fragment.glsl"),
    )
    particle_pipeline = load_pipeline(
        str(shaders_dir / "particle_vertex.glsl"),
        str(shaders_dir / "particle_fragment.glsl"),
    )
    skybox_pipeline = load_pipeline(
        str(shaders_dir / "skybox_vertex.glsl"),
        str(shaders_dir / "skybox_fragment.glsl"),
    )

    # ===== LIGHTING CONFIG =====
    lighting = get_lighting_config()

    # ===== STATIC SCENE =====
    scene_data = build_scene(phong_pipeline)

    # ===== AANG SKINNING =====
    aang_path = str(Path(__file__).parent / "assets" / "avatar_aang_fortnite" / "scene.gltf")
    aang_data = setup_aang(aang_path, skinning_pipeline)
    # Upload Aang textures now that the OpenGL context exists
    aang_data["model"].upload_textures()
    # Apply lotus pose (sitting, legs crossed, hands together)
    apply_lotus_pose(aang_data, pelvis_sink=0.85,
                     facing_deg=scene_mod.AANG_FACING_DEG)

    # Move Aang to the desired world position
    root_name = aang_data["node_to_scenegraph_name"][0]
    aang_data["graph"].nodes[root_name]["transform"] = \
        aang_data["graph"].nodes[root_name]["transform"] @ \
        tr.translate(scene_mod.AANG_POS_X, scene_mod.AANG_POS_Y, scene_mod.AANG_POS_Z)

    # ===== PARTICLES (disabled for static night scene) =====
    # aang_center = scene_data["scene_center"]
    # particle_system = ParticleSystem3D(
    #     max_particles=scene_mod.PARTICLE_MAX,
    #     spawn_center=aang_center,
    #     spawn_radius=scene_mod.PARTICLE_SPAWN_RADIUS,
    #     canopy_height=scene_mod.PARTICLE_CANOPY_HEIGHT,
    # )
    # particle_system.emit(scene_mod.PARTICLE_INITIAL_BURST)
    # particle_renderer = setup_particle_renderer(particle_pipeline, scene_mod.PARTICLE_MAX)

    # ===== SKYBOX =====
    skybox_renderer = setup_skybox(skybox_pipeline)

    # ===== CAMERA =====
    min_pt, max_pt = compute_aang_bbox(aang_data)
    center = (min_pt + max_pt) * 0.5
    diagonal = float(np.linalg.norm(max_pt - min_pt))
    if diagonal <= 0:
        diagonal = 5.0
    camera_offset = np.array([
        diagonal * scene_mod.CAMERA_OFFSET_X_MULT,
        diagonal * scene_mod.CAMERA_OFFSET_Y_MULT,
        diagonal * scene_mod.CAMERA_OFFSET_Z_MULT,
    ], dtype=np.float32)
    initial_eye = center + camera_offset

    camera = LoFiCamera(
        width, height,
        target=center.astype(np.float64),
        initial_eye=initial_eye.astype(np.float64),
        scene_scale=diagonal,
    )
    projection = tr.perspective(
        scene_mod.CAMERA_FOV_DEG, width / height,
        max(diagonal * 0.01, 0.05), max(diagonal * 10.0, 100.0),
    )

    # ===== AUDIO (disabled for static scene) =====
    # audio_path = str(Path(__file__).parent / "assets" / "audio" / "lofi.mp3")
    # audio_player = load_lofi_audio(audio_path)
    audio_player = None

    # ===== SKIN MATRICES BUFFER =====
    n_joints = aang_data["n_joints"]
    Mat4Array = (GLfloat * 16) * n_joints
    skin_matrices_buffer = Mat4Array()
    skin_matrices_view = np.frombuffer(skin_matrices_buffer, dtype=np.float32).reshape(n_joints, 16)

    # ===== STATE =====
    state = {"time": 0.0, "paused": False, "audio_on": audio_player is not None}

    # ===== HUD LABELS =====
    title_label = pyglet.text.Label(
        "Aang Meditando — Lo-Fi",
        font_name="Fira Code", font_size=16,
        x=12, y=height - 24, color=(255, 240, 180, 255),
    )
    help_label = pyglet.text.Label(
        "WASD: mover | Mouse: orbitar | Rueda: zoom | R: reset | SPACE: pausa | M: audio | ESC: salir",
        font_name="Fira Code", font_size=11,
        x=12, y=18, color=(180, 200, 220, 255),
    )

    # ===== SETUP LIGHTING HELPER (local) =====
    def set_lighting_here(pipeline, lighting_cfg, camera_pos, view, proj):
        pipeline["view"] = view.reshape(16, 1, order="F")
        pipeline["projection"] = proj.reshape(16, 1, order="F")
        pipeline["light_direction"] = lighting_cfg["light_direction"].reshape(3, 1, order="F")
        pipeline["light_color"] = lighting_cfg["light_color"].reshape(3, 1, order="F")
        pipeline["camera_position"] = camera_pos.reshape(3, 1, order="F")
        pipeline["ambient_strength"] = lighting_cfg["ambient_strength"]
        pipeline["shininess"] = lighting_cfg["shininess"]
        pipeline["fog_color"] = lighting_cfg["fog_color"].reshape(4, 1, order="F")
        pipeline["fog_near"] = lighting_cfg["fog_near"]
        pipeline["fog_far"] = lighting_cfg["fog_far"]
        pipeline["base_color_factor"] = np.array([1, 1, 1], dtype=np.float32).reshape(3, 1, order="F")
        pipeline["alpha_cutoff"] = 0.01

    # ===== EVENT HANDLERS =====
    @window.event
    def on_mouse_press(x, y, button, modifiers):
        camera.on_mouse_press(x, y, button, modifiers)

    @window.event
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        camera.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    @window.event
    def on_mouse_scroll(x, y, scroll_x, scroll_y):
        camera.on_mouse_scroll(x, y, scroll_x, scroll_y)

    @window.event
    def on_key_press(symbol, modifiers):
        camera.on_key_press_WASD(symbol)
        # Global keys
        if symbol == pyglet.window.key.R:
            camera.reset()
        elif symbol == pyglet.window.key.SPACE:
            state["paused"] = not state["paused"]
        elif symbol == pyglet.window.key.M:
            if audio_player is not None:
                audio_mod.toggle_audio(audio_player)
                state["audio_on"] = audio_player.playing
        elif symbol == pyglet.window.key.ESCAPE:
            window.close()

    @window.event
    def on_key_release(symbol, modifiers):
        camera.on_key_release_WASD(symbol)

    @window.event
    def on_draw():
        window.clear()
        # Skybox nocturno: se renderiza primero con depth test off
        render_skybox(skybox_renderer, camera.get_view_matrix(), projection, state["time"])

        view = camera.get_view_matrix()
        # Extract camera world position from view matrix inverse (pose)
        camera_pos = camera.arcball.pose[:3, 3]

        # ---- Draw static objects (Phong pipeline) ----
        phong_pipeline.use()
        set_lighting_here(phong_pipeline, lighting, camera_pos, view, projection)

        # Sort: opaque first, transparent last
        opaque = [p for p in scene_data["primitives"] if not p.get("is_transparent", False)]
        transparent = [p for p in scene_data["primitives"] if p.get("is_transparent", False)]

        for prim in opaque + transparent:
            if prim.get("is_transparent"):
                GL.glDepthMask(GL.GL_FALSE)
            else:
                GL.glDepthMask(GL.GL_TRUE)

            phong_pipeline["transform"] = prim["transform"].reshape(16, 1, order="F")
            if "base_color_factor" in prim:
                bcf = prim["base_color_factor"]
                # Shader expects vec3; scene_builder may store vec4 (RGBA)
                phong_pipeline["base_color_factor"] = np.array(bcf[:3], dtype=np.float32).reshape(3, 1, order="F")
            else:
                phong_pipeline["base_color_factor"] = np.array([1, 1, 1], dtype=np.float32).reshape(3, 1, order="F")

            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, prim["texture_id"])
            prim["vertex_list"].draw(GL.GL_TRIANGLES)

        GL.glDepthMask(GL.GL_TRUE)

        # ---- Draw Aang (skinning pipeline) ----
        apply_breathing_and_wind(aang_data, state["time"], first_call=(state["time"] < 0.02))

        skin_matrices, _, _ = compute_skin_matrices(aang_data)
        skin_matrices_view[:] = skin_matrices.transpose(0, 2, 1).reshape(n_joints, 16)

        skinning_pipeline.use()
        skinning_pipeline["view"] = view.reshape(16, 1, order="F")
        skinning_pipeline["projection"] = projection.reshape(16, 1, order="F")
        skinning_pipeline["transform"] = tr.identity().reshape(16, 1, order="F")
        skinning_pipeline["skin_matrices"] = skin_matrices_buffer
        setup_lighting(skinning_pipeline, lighting, camera_pos)
        skinning_pipeline["shininess"] = 2.0
        skinning_pipeline["ambient_strength"] = 0.65
        skinning_pipeline["specular_strength"] = 0.08
        skinning_pipeline["base_color_factor"] = np.array([1, 1, 1], dtype=np.float32).reshape(3, 1, order="F")
        skinning_pipeline["alpha_cutoff"] = 0.01
        skinning_pipeline["diffuse_texture"] = 0

        for prim in aang_data["primitives"]:
            tex_id = None
            if prim.get("material_index") is not None:
                mat = aang_data["model"].materials[prim["material_index"]]
                tex_idx = mat.get("base_color_texture")
                if tex_idx is not None and aang_data["model"].texture_gl_ids:
                    tex_id = aang_data["model"].texture_gl_ids[tex_idx]
            if tex_id is not None:
                GL.glActiveTexture(GL.GL_TEXTURE0)
                GL.glBindTexture(GL.GL_TEXTURE_2D, tex_id)
            prim["vertex_list"].draw(GL.GL_TRIANGLES)

        # ---- Draw particles (disabled) ----
        # if not state["paused"]:
        #     particle_system.update(0.016)
        # render_particles(particle_renderer, particle_system, view, projection, point_size_scale=scene_mod.PARTICLE_POINT_SIZE_SCALE)

        # ---- HUD ----
        with ui_overlay():
            title_label.draw()
            help_label.draw()

    # ===== UPDATE LOOP =====
    def update(dt):
        if not state["paused"]:
            state["time"] += dt
        camera.update(dt)

    pyglet.clock.schedule_interval(update, 1.0 / 60.0)
    pyglet.app.run()
