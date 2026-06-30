#version 330

in vec4 frag_color;
in float frag_depth;

out vec4 out_color;

void main()
{
    // Procedural soft circle via gl_PointCoord
    float d = length(gl_PointCoord - vec2(0.5));

    // Discard pixels outside the circle
    if (d > 0.5) discard;

    // Smooth alpha falloff at the circle edge
    float alpha = smoothstep(0.5, 0.0, d) * frag_color.a;

    // Depth attenuation: particles fade with distance
    alpha *= exp(-frag_depth * 0.01);

    out_color = vec4(frag_color.rgb, alpha);
}
