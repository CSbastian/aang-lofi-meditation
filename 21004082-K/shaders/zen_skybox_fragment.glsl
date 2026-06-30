#version 330

// Fragment shader del skybox zen con crossfade entre texturas.

in vec2 v_uv;

uniform sampler2D u_texture;
uniform float u_blend;

out vec4 out_color;

void main() {
    vec3 tex_color = texture(u_texture, v_uv).rgb;
    // Aplicar alpha segun u_blend (para crossfade)
    out_color = vec4(tex_color, u_blend);
}
