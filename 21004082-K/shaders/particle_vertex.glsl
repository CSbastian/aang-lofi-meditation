#version 330

uniform mat4 view;
uniform mat4 projection;
uniform float point_size_scale;

in vec3 position;
in vec4 color;
in float size;

out vec4 frag_color;
out float frag_depth;

void main()
{
    vec4 view_pos = view * vec4(position, 1.0);
    gl_Position = projection * view_pos;

    // Distance-based size attenuation: farther = smaller
    gl_PointSize = point_size_scale * size / gl_Position.w;

    frag_color = color;
    frag_depth = -view_pos.z;
}
