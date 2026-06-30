#version 330

in vec3 world_position;
in vec3 world_normal;
in vec2 frag_uv;

uniform sampler2D diffuse_texture;
uniform vec3 base_color_factor;
uniform vec3 light_direction;
uniform vec3 light_color;
uniform vec3 camera_position;
uniform float ambient_strength;
uniform float shininess;
uniform vec4 fog_color;
uniform float fog_near;
uniform float fog_far;
uniform float alpha_cutoff;

out vec4 out_color;

void main()
{
    vec4 sampled = texture(diffuse_texture, frag_uv);

    // Descartar pixeles practicamente invisibles (no escriben al depth buffer)
    if (sampled.a < alpha_cutoff) {
        discard;
    }

    vec3 albedo = sampled.rgb * base_color_factor;
    vec3 normal = normalize(world_normal);
    vec3 light_dir = normalize(light_direction);

    // Componente ambiental
    vec3 ambient = ambient_strength * light_color * albedo;

    // Componente difusa (ley de Lambert)
    float diff = max(dot(normal, light_dir), 0.0);
    vec3 diffuse = diff * light_color * albedo;

    // Componente especular (modelo Phong)
    vec3 view_dir = normalize(camera_position - world_position);
    vec3 reflect_dir = reflect(-light_dir, normal);
    float spec = pow(max(dot(reflect_dir, view_dir), 0.0), shininess);
    vec3 specular = spec * light_color;

    // Combinar iluminacion Phong
    vec3 phong_color = ambient + diffuse + specular;

    // Niebla lineal basada en profundidad (distancia desde la camara)
    float depth = length(world_position - camera_position);
    float fog_factor = clamp(smoothstep(fog_near, fog_far, depth), 0.0, 1.0);

    out_color = vec4(mix(phong_color, fog_color.rgb, fog_factor), sampled.a);
}
