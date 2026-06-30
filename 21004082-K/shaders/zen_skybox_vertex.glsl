#version 330

// Skybox zen con textura equirectangular.
// Renderiza el cielo con UVs equirectangulares y soporta crossfade
// entre dos texturas para transiciones suaves dia-noche.

in vec3 position;
in vec2 uv;

uniform mat4 u_projection;
uniform mat4 u_view;
uniform sampler2D u_texture;
uniform float u_blend;  // 0 = textura 1 full, 1 = textura 2 full

out vec2 v_uv;

void main() {
    // La esfera esta en world space, pero la view matrix no debe aplicar
    // traslacion para que el skydome parezca estar en el infinito.
    vec4 view_pos = u_view * vec4(position, 1.0);
    gl_Position = u_projection * view_pos;
    v_uv = uv;
}
