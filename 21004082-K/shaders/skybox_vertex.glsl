#version 330

// Vertex shader para skydome.
// El skydome sigue a la cámara: se desactiva la traslación de view matrix.

in vec3 position;

uniform mat4 u_projection;
uniform mat4 u_view;       // solo la rotación, no la traslación

out vec3 world_position;
out vec3 world_normal;

void main() {
    vec4 view_pos = u_view * vec4(position, 1.0);
    gl_Position = u_projection * view_pos;

    world_position = position;
    world_normal = normalize(position);
}
