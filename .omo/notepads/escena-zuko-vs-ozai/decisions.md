# Decisions Log

## 2026-06-24: Asset model selection

**Decision**: Use repo primitives (`assets/cube.off`, `assets/sphere.off`,
`assets/cylinder.off`) instead of downloading 3D character models for
Zuko and Ozai.

**Rationale**:
- Models found on Sketchfab require interactive browser (not CLI-automatable)
- CGTrader model has restrictive "no AI" license
- No free Ozai model found
- Characters need separate articulated body parts (not single mesh)
- Primitives map naturally: cube→torso, sphere→head, cylinder→arms/legs
- `force_color` parameter in `_node_from_file` enables Fire Nation palette
  without textures

**Impact**: Characters will be stylized/blocky (primitive-based) rather
than realistic. This matches the educational nature of the project and
avoids licensing issues.
