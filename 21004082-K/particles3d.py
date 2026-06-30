"""Sistema de partículas 3D para hojas cayendo.

Adapta el patrón Structure-of-Arrays (SoA) de `grafica/particle.py` a un
sistema de partículas que caen como pequeñas hojas. Las partículas caen
con turbulencia lateral, rebotan suavemente en el suelo, y se re-emiten
desde arriba para mantener la densidad visual.
"""

import numpy as np


def setup_particle_renderer(particle_pipeline, max_particles):
    """Crea los recursos GPU para renderizar partículas como ``GL_POINTS``.

    Args:
        particle_pipeline: ``pyglet.graphics.shader.ShaderProgram`` ya
            compilado y linkeado con el vertex/fragment de partículas.
            Debe declarar los atributos ``position`` (vec3), ``color``
            (vec4) y ``size`` (float), más los uniforms ``view``,
            ``projection`` y ``point_size_scale``.
        max_particles (int): Tamaño del pool (coincide con
            ``ParticleSystem3D.max_particles``).

    Returns:
        dict: con claves ``"pipeline"``, ``"vertex_list"`` y
        ``"max_particles"``. El diccionario lo consume
        :func:`render_particles`.
    """
    import pyglet.gl as GL

    vl = particle_pipeline.vertex_list(
        max_particles, GL.GL_POINTS,
        position="f",  # vec3
        color="f",     # vec4
        size="f",      # float
    )
    return {
        "pipeline": particle_pipeline,
        "vertex_list": vl,
        "max_particles": max_particles,
    }


def render_particles(
    renderer,
    particle_system,
    view,
    projection,
    point_size_scale=10.0,
):
    """Sube los datos activos del sistema a la GPU y dibuja ``GL_POINTS``.

    Llamar **después** de ``particle_system.update(dt)`` en el loop de
    dibujo. Si no hay partículas activas, no hace nada. El ``count`` de
    dibujo se acota al ``max_particles`` del renderer para no overflowear
    el buffer reservado en :func:`setup_particle_renderer`.

    Args:
        renderer (dict): Estructura devuelta por
            :func:`setup_particle_renderer`.
        particle_system: Instancia de :class:`ParticleSystem3D`.
        view (np.ndarray): Matriz de vista 4×4 (``np.linalg.inv(pose)``
            de la cámara).
        projection (np.ndarray): Matriz de proyección 4×4.
        point_size_scale (float): Multiplicador global de tamaño de
            punto. ``10.0`` da puntos visibles a escala humana.
    """
    import pyglet.gl as GL

    pipeline = renderer["pipeline"]
    vl = renderer["vertex_list"]
    max_n = renderer["max_particles"]

    positions, colors, sizes = particle_system.get_gpu_data()
    n = particle_system.draw_count()

    if n == 0:
        return

    # Clamp al tamaño del buffer GPU reservado
    n = min(n, max_n)

    # El vertex_list tiene tamaño fijo max_n. Si hay menos partículas
    # activas que el buffer, rellenamos con ceros para que la asignación
    # no falle. Las particulas sobrantes son invisibles
    # (posicion origen, size=0, alpha=0).
    pad = max_n - n
    if pad > 0:
        positions = np.vstack([positions[:n], np.zeros((pad, 3), dtype=np.float32)])
        colors = np.vstack([colors[:n], np.zeros((pad, 4), dtype=np.float32)])
        sizes = np.hstack([sizes[:n], np.zeros(pad, dtype=np.float32)])

    vl.position[:] = positions[:max_n].flatten()
    vl.color[:] = colors[:max_n].flatten()
    vl.size[:] = sizes[:max_n].flatten()

    pipeline.use()
    pipeline["view"] = view.reshape(16, 1, order="F")
    pipeline["projection"] = projection.reshape(16, 1, order="F")
    pipeline["point_size_scale"] = point_size_scale

    vl.draw(GL.GL_POINTS)


class ParticleSystem3D:
    """Sistema de partículas 3D: hojas cayendo con turbulencia.

    Las particulas caen desde arriba con deriva lateral, fluttering,
    y se detienen al tocar el suelo (Y=0).  Despues de un tiempo en
    el suelo, desaparecen y se re-emiten desde el dosel.

    Args:
        max_particles (int): Tamaño maximo del pool.
        spawn_center (array-like): Centro de emision [x, y, z].
        spawn_radius (float): Radio horizontal de emision.
        canopy_height (float): Altura desde la que caen las hojas
            (relativa a spawn_center.y).
    """

    def __init__(self, max_particles, spawn_center, spawn_radius, canopy_height):
        self.max_particles = max_particles
        self.spawn_center = np.array(spawn_center, dtype=np.float32)
        self.spawn_radius = spawn_radius
        self.canopy_height = canopy_height  # altura de spawn relativa al centro

        N = max_particles
        self.positions = np.zeros((N, 3), dtype=np.float32)
        self.velocities = np.zeros((N, 3), dtype=np.float32)
        self.colors = np.ones((N, 4), dtype=np.float32)
        self.sizes = np.ones(N, dtype=np.float32) * 3.0
        self.ages = np.zeros(N, dtype=np.float32)
        self.ttls = np.zeros(N, dtype=np.float32)
        self.grounded = np.zeros(N, dtype=bool)  # ya toco el suelo?
        self.active = np.zeros(N, dtype=bool)
        self.time = 0.0

    def emit(self, n):
        """Emite hasta n particulas desde arriba (dosel de arboles)."""
        inactive = np.where(~self.active)[0][:n]
        m = len(inactive)
        if m == 0:
            return

        angles = np.random.uniform(0, 2 * np.pi, m)
        radii = np.random.uniform(0, self.spawn_radius, m)
        self.positions[inactive, 0] = self.spawn_center[0] + radii * np.cos(angles)
        self.positions[inactive, 1] = self.spawn_center[1] + self.canopy_height + np.random.uniform(0, 2.0, m)
        self.positions[inactive, 2] = self.spawn_center[2] + radii * np.sin(angles)

        # Caida lenta con deriva lateral (hoja planeando)
        self.velocities[inactive, 1] = np.random.uniform(-0.15, -0.05, m)  # cae
        self.velocities[inactive, 0] = np.random.uniform(-0.10, 0.10, m)  # deriva X
        self.velocities[inactive, 2] = np.random.uniform(-0.10, 0.10, m)  # deriva Z

        # Colores de hoja natural: verdes con algo de amarillo
        t = np.random.random(m)
        self.colors[inactive, 0] = 0.20 + 0.15 * np.random.random(m)         # R: 0.20-0.35
        self.colors[inactive, 1] = 0.35 + 0.30 * np.random.random(m)         # G: 0.35-0.65
        self.colors[inactive, 2] = 0.10 + 0.15 * np.random.random(m)         # B: 0.10-0.25
        self.colors[inactive, 3] = 0.55 + 0.15 * np.random.random(m)         # A: 0.55-0.70

        # Mas grandes: 6 a 18
        self.sizes[inactive] = np.random.uniform(6.0, 18.0, m)
        self.ttls[inactive] = np.random.uniform(10.0, 20.0, m)
        self.ages[inactive] = 0.0
        self.grounded[inactive] = False
        self.active[inactive] = True

    def update(self, dt):
        """Avanza la simulacion. Las hojas caen, fluttean, y se posan en el suelo."""
        self.time += dt
        active_mask = self.active

        # 1) Integrar posicion
        self.positions[active_mask] += self.velocities[active_mask] * dt

        # 2) Turbulencia lateral (fluttering de hoja)
        idx = np.where(active_mask & ~self.grounded)[0]
        if len(idx) > 0:
            self.velocities[idx, 0] += np.sin(self.time * 3.0 + idx * 0.3) * dt * 0.08
            self.velocities[idx, 2] += np.cos(self.time * 3.0 + idx * 0.3) * dt * 0.08

        # 3) Colision con el suelo (Y <= 0)
        hit_ground = self.positions[:, 1] <= 0.0
        newly_grounded = hit_ground & active_mask & ~self.grounded
        if newly_grounded.any():
            self.positions[newly_grounded, 1] = 0.0
            self.velocities[newly_grounded, 1] = 0.0
            self.velocities[newly_grounded, 0] = np.random.uniform(-0.02, 0.02, newly_grounded.sum())
            self.velocities[newly_grounded, 2] = np.random.uniform(-0.02, 0.02, newly_grounded.sum())
            self.grounded[newly_grounded] = True

        # 4) Envejecimiento y muerte
        self.ages[active_mask] += dt
        exceeded_ttl = self.ages > self.ttls
        # Particulas en el suelo mueren mas rapido (~3s extra)
        ground_death = self.grounded & (self.ages > self.ttls * 0.6)
        self.active[exceeded_ttl | ground_death] = False

        # 5) Auto-respawn para mantener densidad
        active_count = int(self.active.sum())
        deficit = self.max_particles - active_count
        if deficit > self.max_particles * 0.3:
            self.emit(min(deficit, self.max_particles // 5))

    def get_gpu_data(self):
        """Devuelve tuplas ``(positions, colors, sizes)`` filtradas por activas.

        Los arrays ya están contiguos en dtype ``np.float32`` y se pueden
        subir directamente a un ``pyglet.graphics.vertex_list`` con
        ``GL_POINTS`` (tarea 3). Se devuelve una copia para que mutaciones
        internas no rompan la subida ya realizada.
        """
        active_mask = self.active
        if not active_mask.any():
            empty_pos = np.zeros((0, 3), dtype=np.float32)
            empty_col = np.zeros((0, 4), dtype=np.float32)
            empty_sz = np.zeros(0, dtype=np.float32)
            return (empty_pos, empty_col, empty_sz)
        return (
            self.positions[active_mask].copy(),
            self.colors[active_mask].copy(),
            self.sizes[active_mask].copy(),
        )

    def draw_count(self):
        """Número de partículas activas listas para dibujar este frame."""
        return int(self.active.sum())
