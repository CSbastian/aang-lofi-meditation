#version 330

// Skydome con estrellas procedurales estaticas (sin titilato).
// Renderiza el cielo nocturno como un cascarón esferico.
// Las estrellas se generan con hash deterministico por direccion.
// Colores realistas segun tipo espectral (blancos y azulados).

in vec3 world_position;
in vec3 world_normal;

uniform float u_time;
uniform float u_star_density;
uniform float u_star_brightness;
uniform float u_cycle_duration;

out vec4 out_color;

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

vec2 hash22(vec2 p) {
    return vec2(hash21(p), hash21(p + 17.17));
}

vec2 dir_to_sphere(vec3 d) {
    d = normalize(d);
    float theta = atan(d.z, d.x);
    float phi = acos(clamp(d.y, -1.0, 1.0));
    return vec2(theta, phi);
}

vec3 star_color(float seed) {
    // Estrellas azuladas: mas B que A o F, y un toque violeta para variedad
    if (seed < 0.20) return vec3(0.50, 0.60, 1.00);   // azul fuerte
    if (seed < 0.50) return vec3(0.70, 0.80, 1.00);   // blanco-azul
    if (seed < 0.85) return vec3(0.80, 0.90, 1.00);   // blanco
    return vec3(0.75, 0.85, 1.00);                     // blanco-azul palido
}

vec4 star_at(vec2 uv, float density, vec2 seed_offset) {
    vec2 cell = floor(uv * density);
    vec2 cell_uv = fract(uv * density);
    vec2 rand = hash22(cell + seed_offset);
    vec2 star_pos = vec2(0.5) + (rand - 0.5) * 0.8;
    float d = distance(cell_uv, star_pos);
    float radius = 0.02 + rand.x * 0.03;
    float brightness = exp(-d * d / (radius * radius));
    vec3 color = star_color(hash21(cell + seed_offset * 0.3));
    return vec4(brightness, color);
}

void main() {
    vec3 dir = normalize(world_position);
    float t = clamp(dir.y * 0.5 + 0.5, 0.0, 1.0);

    // Ciclo dia-noche: t01 va de 0 a 1
    float t01 = mod(u_time / u_cycle_duration, 1.0);

    // Colores del cielo por momento del dia
    vec3 dawn_top    = vec3(0.70, 0.50, 0.50);
    vec3 dawn_horiz  = vec3(0.86, 0.62, 0.47);
    vec3 day_top     = vec3(0.39, 0.58, 0.86);
    vec3 day_horiz   = vec3(0.78, 0.86, 0.98);
    vec3 dusk_top    = vec3(0.31, 0.23, 0.39);
    vec3 dusk_horiz  = vec3(0.94, 0.58, 0.31);
    vec3 night_top   = vec3(0.03, 0.03, 0.10);
    vec3 night_horiz = vec3(0.08, 0.10, 0.18);

    vec3 sky_top, sky_horiz;
    float star_vis;

    if (t01 < 0.25) {
        float k = t01 / 0.25;
        sky_top  = mix(dawn_top,  day_top,    k);
        sky_horiz = mix(dawn_horiz, day_horiz, k);
        star_vis = 1.0 - k;
    } else if (t01 < 0.5) {
        float k = (t01 - 0.25) / 0.25;
        sky_top  = mix(day_top,   dusk_top,    k);
        sky_horiz = mix(day_horiz, dusk_horiz, k);
        star_vis = k * 0.3;
    } else if (t01 < 0.75) {
        float k = (t01 - 0.5) / 0.25;
        sky_top  = mix(dusk_top,   night_top,    k);
        sky_horiz = mix(dusk_horiz, night_horiz, k);
        star_vis = 0.3 + k * 0.7;
    } else {
        float k = (t01 - 0.75) / 0.25;
        sky_top  = mix(night_top,  dawn_top,    k);
        sky_horiz = mix(night_horiz, dawn_horiz, k);
        star_vis = 1.0 - k * 0.3;
    }

    vec3 sky = mix(sky_horiz, sky_top, t);

    // Estrellas
    vec2 sphere = dir_to_sphere(dir);
    vec2 star_uv = sphere * vec2(50.0, 25.0);
    vec4 s1 = star_at(star_uv,            u_star_density,        vec2(1.0, 0.0));
    vec4 s2 = star_at(star_uv * 1.7,      u_star_density * 0.6,  vec2(2.0, 0.0));
    vec4 s3 = star_at(star_uv * 2.3,      u_star_density * 0.3,  vec2(3.0, 0.0));
    vec3 stars_rgb = s1.yzw * s1.x + s2.yzw * s2.x + s3.yzw * s3.x;
    float visibility = smoothstep(-0.3, 0.1, dir.y) * star_vis;
    stars_rgb *= visibility;

    vec3 color = sky + stars_rgb * u_star_brightness;
    out_color = vec4(color, 1.0);
}
