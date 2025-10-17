#!/usr/bin/env python3
"""
Simple Wavefront OBJ viewer in Python using pygame + PyOpenGL,
now with **texture map** support.

Controls
--------
Arrow Keys: rotate around X/Y axes (↑/↓ = X, ←/→ = Y)
A / D     : rotate around Z axis (A = +Z, D = -Z)
W / S     : dolly in / out (change camera distance)
R         : reset view
Esc / Q   : quit

Usage
-----
python pygame_obj_viewer.py path/to/doll.obj
(The .mtl file should sit next to the .obj and be referenced via `mtllib`.)

Notes
-----
- Supports v / vt / vn, faces with 3+ vertices (fan-triangulated), and a subset of MTL:
  - newmtl, Kd (diffuse color), Ka (ambient), Ks (specular), Ns (shininess), d/Tr (alpha), illum, **map_Kd (diffuse texture)**
- Textures are applied per-material. If a face's material has map_Kd, the mesh will render textured; otherwise it uses flat color + lighting.
- Supported image formats: anything pygame can load (PNG/JPG recommended).
- OBJ's `vt` V coordinate is flipped to match OpenGL's origin.

"""

import math
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import DOUBLEBUF, OPENGL

Color3 = Tuple[float, float, float]


@dataclass
class Material:
    name: str
    Kd: Color3 = (0.8, 0.8, 0.8)  # diffuse color
    Ka: Color3 = (0.2, 0.2, 0.2)  # ambient
    Ks: Color3 = (0.0, 0.0, 0.0)  # specular
    Ns: float = 0.0  # shininess
    d: float = 1.0  # alpha
    illum: int = 2
    map_Kd: Optional[str] = None  # path to diffuse texture
    _tex_id: Optional[int] = None  # OpenGL texture id (filled later)


@dataclass
class Face:
    # Indices are 0-based
    v_idx: List[int]
    vt_idx: List[int]
    vn_idx: List[int]
    material: Optional[str]


@dataclass
class Mesh:
    vertices: List[Tuple[float, float, float]] = field(default_factory=list)
    texcoords: List[Tuple[float, float]] = field(default_factory=list)
    normals: List[Tuple[float, float, float]] = field(default_factory=list)
    faces: List[Face] = field(default_factory=list)
    materials: Dict[str, Material] = field(default_factory=dict)

    def ensure_normals(self):
        if self.normals:
            return
        # Compute per-face normals then assign per-vertex normals (simple average)
        v_count = len(self.vertices)
        accum = [[0.0, 0.0, 0.0] for _ in range(v_count)]
        ref_count = [0 for _ in range(v_count)]

        def cross(a, b):
            return (
                a[1] * b[2] - a[2] * b[1],
                a[2] * b[0] - a[0] * b[2],
                a[0] * b[1] - a[1] * b[0],
            )

        def normalize(v):
            l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
            if l == 0:
                return (0.0, 0.0, 1.0)
            return (v[0] / l, v[1] / l, v[2] / l)

        for f in self.faces:
            if len(f.v_idx) < 3:
                continue
            i0, i1, i2 = f.v_idx[0], f.v_idx[1], f.v_idx[2]
            p0, p1, p2 = self.vertices[i0], self.vertices[i1], self.vertices[i2]
            e1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
            e2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
            n = cross(e1, e2)
            n = normalize(n)
            for idx in f.v_idx:
                accum[idx][0] += n[0]
                accum[idx][1] += n[1]
                accum[idx][2] += n[2]
                ref_count[idx] += 1

        self.normals = []
        for i in range(v_count):
            if ref_count[i] == 0:
                self.normals.append((0.0, 0.0, 1.0))
            else:
                n = (
                    accum[i][0] / ref_count[i],
                    accum[i][1] / ref_count[i],
                    accum[i][2] / ref_count[i],
                )
                self.normals.append(normalize(n))

        # write vn indices if faces had none
        for f in self.faces:
            if not f.vn_idx or len(f.vn_idx) != len(f.v_idx):
                f.vn_idx = list(f.v_idx)


class OBJLoader:
    def __init__(self, obj_path: str):
        self.obj_path = obj_path
        self.base_dir = os.path.dirname(os.path.abspath(obj_path))

    def load(self) -> Mesh:
        mesh = Mesh()
        current_mtl: Optional[str] = None

        def parse_f(tokens: List[str]):
            # Supports: v, v/vt, v//vn, v/vt/vn
            v_idx, vt_idx, vn_idx = [], [], []
            for t in tokens:
                parts = t.split("/")
                vi = int(parts[0])
                vi = (
                    vi - 1 if vi > 0 else vi
                )  # OBJ indices can be negative (relative)
                if vi < 0:
                    vi = len(mesh.vertices) + vi + 1 - 1
                v_idx.append(vi)

                if len(parts) > 1 and parts[1]:
                    ti = int(parts[1])
                    ti = ti - 1 if ti > 0 else ti
                    if ti < 0:
                        ti = len(mesh.texcoords) + ti + 1 - 1
                    vt_idx.append(ti)
                else:
                    vt_idx.append(-1)

                if len(parts) > 2 and parts[2]:
                    ni = int(parts[2])
                    ni = ni - 1 if ni > 0 else ni
                    if ni < 0:
                        ni = len(mesh.normals) + ni + 1 - 1
                    vn_idx.append(ni)
                else:
                    vn_idx.append(-1)
            return v_idx, vt_idx, vn_idx

        # First pass: read geometry + remember referenced MTL
        mtl_files: List[str] = []
        with open(self.obj_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                tag = parts[0]
                if tag == "v":
                    x, y, z = map(float, parts[1:4])
                    mesh.vertices.append((x, y, z))
                elif tag == "vt":
                    u, v = map(float, parts[1:3])
                    mesh.texcoords.append((u, 1.0 - v))  # flip V for OpenGL
                elif tag == "vn":
                    nx, ny, nz = map(float, parts[1:4])
                    mesh.normals.append((nx, ny, nz))
                elif tag == "f":
                    v_idx, vt_idx, vn_idx = parse_f(parts[1:])
                    # fan triangulate if needed
                    if len(v_idx) >= 3:
                        for i in range(1, len(v_idx) - 1):
                            tri_v = [v_idx[0], v_idx[i], v_idx[i + 1]]
                            tri_vt = [vt_idx[0], vt_idx[i], vt_idx[i + 1]]
                            tri_vn = [vn_idx[0], vn_idx[i], vn_idx[i + 1]]
                            mesh.faces.append(
                                Face(tri_v, tri_vt, tri_vn, current_mtl)
                            )
                elif tag == "usemtl":
                    current_mtl = parts[1]
                elif tag == "mtllib":
                    mtl_files.append(" ".join(parts[1:]))
                # ignore o, g, s, etc.

        # Load MTL files
        for mtl_name in mtl_files:
            mtl_path = os.path.join(self.base_dir, mtl_name)
            if os.path.exists(mtl_path):
                self._load_mtl(mtl_path, mesh)

        # Fill missing normals
        mesh.ensure_normals()
        return mesh

    def _load_mtl(self, mtl_path: str, mesh: Mesh):
        current: Optional[Material] = None
        base_dir = os.path.dirname(mtl_path)
        with open(mtl_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                tag = parts[0]
                if tag == "newmtl":
                    if current:
                        mesh.materials[current.name] = current
                    current = Material(name=" ".join(parts[1:]))
                elif tag == "Kd" and current:
                    current.Kd = tuple(map(float, parts[1:4]))  # type: ignore
                elif tag == "Ka" and current:
                    current.Ka = tuple(map(float, parts[1:4]))  # type: ignore
                elif tag == "Ks" and current:
                    current.Ks = tuple(map(float, parts[1:4]))  # type: ignore
                elif tag == "Ns" and current:
                    current.Ns = float(parts[1])
                elif tag in ("d", "Tr") and current:
                    # Some exporters use Tr = 1 - d
                    val = float(parts[1])
                    current.d = 1.0 - val if tag == "Tr" else val
                elif tag == "illum" and current:
                    try:
                        current.illum = int(parts[1])
                    except ValueError:
                        current.illum = 2
                elif tag == "map_Kd" and current:
                    # Join rest of the line to allow spaces and options; ignore
                    # options for simplicity
                    tex_name = " ".join(parts[1:]).split()[-1]
                    # Resolve relative to the MTL file's directory
                    current.map_Kd = os.path.normpath(
                        os.path.join(base_dir, tex_name)
                    )
            if current:
                mesh.materials[current.name] = current


def setup_gl(width: int, height: int):
    glViewport(0, 0, width, height)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    glEnable(GL_NORMALIZE)

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 5.0, 10.0, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (0.8, 0.8, 0.8, 1.0))

    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glClearColor(0.05, 0.06, 0.08, 1.0)


def set_perspective(
    width: int,
    height: int,
    fov: float = 60.0,
    znear: float = 0.1,
    zfar: float = 1000.0,
):
    aspect = width / float(height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fov, aspect, znear, zfar)
    glMatrixMode(GL_MODELVIEW)


def load_texture(image_path: str) -> Optional[int]:
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        surf = pygame.image.load(image_path)
        surf = (
            surf.convert_alpha()
            if surf.get_flags() & pygame.SRCALPHA
            else surf.convert()
        )
        img_data = pygame.image.tostring(surf, "RGBA", True)
        width, height = surf.get_size()

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(
            GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            img_data,
        )
        # Generate mipmaps if available
        try:
            glGenerateMipmap(GL_TEXTURE_2D)
        except Exception:
            pass
        glBindTexture(GL_TEXTURE_2D, 0)
        return tex_id
    except Exception as e:
        print(f"Failed to load texture '{image_path}': {e}")
        return None


class Renderer:
    def __init__(self, mesh: Mesh):
        self.mesh = mesh
        for m in self.mesh.materials.values():
            if m.map_Kd and m._tex_id is None:
                m._tex_id = load_texture(m.map_Kd)

        self.disp_list = glGenLists(1)
        glNewList(self.disp_list, GL_COMPILE)
        self._build_display_list()
        glEndList()

    def _apply_material(self, mtl_name: Optional[str]):
        m = self.mesh.materials.get(mtl_name, None) if mtl_name else None
        if m:
            kd = (*m.Kd, m.d)
            ks = (*m.Ks, 1.0)
            glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, kd)
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, ks)
            shininess = max(0.0, min(128.0, m.Ns))
            glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, shininess)
            glColor4f(*kd)
            # Texturing
            if m._tex_id:
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, m._tex_id)
                glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
            else:
                glDisable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, 0)
            # Alpha blending if needed
            if m.d < 1.0:
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            else:
                glDisable(GL_BLEND)
        else:
            glDisable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_BLEND)
            glColor4f(0.8, 0.8, 0.85, 1.0)
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))
            glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 0.0)

    def _build_display_list(self):
        # Group faces by material for fewer state changes
        by_mtl: Dict[Optional[str], List[Face]] = {}
        for f in self.mesh.faces:
            by_mtl.setdefault(f.material, []).append(f)

        for mtl_name, faces in by_mtl.items():
            self._apply_material(mtl_name)
            glBegin(GL_TRIANGLES)
            for f in faces:
                for j in range(3):
                    # Normal
                    ni = f.vn_idx[j] if j < len(f.vn_idx) else -1
                    if 0 <= ni < len(self.mesh.normals):
                        glNormal3fv(self.mesh.normals[ni])
                    # Texcoord (if any)
                    ti = f.vt_idx[j] if j < len(f.vt_idx) else -1
                    if 0 <= ti < len(self.mesh.texcoords):
                        glTexCoord2fv(self.mesh.texcoords[ti])
                    # Position
                    vi = f.v_idx[j]
                    glVertex3fv(self.mesh.vertices[vi])
            glEnd()

        # After building, unbind texture to leave clean state
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

    def draw(self):
        glCallList(self.disp_list)


@dataclass
class OrbitCamera:
    rot_x: float = 20.0
    rot_y: float = -30.0
    rot_z: float = 0.0
    distance: float = 5.0

    def apply(self, target=(0.0, 0.0, 0.0)):
        glLoadIdentity()
        gluLookAt(0, 0, self.distance, 0, 0, 0, 0, 1, 0)
        glRotatef(self.rot_z, 0, 0, 1)
        glRotatef(self.rot_x, 1, 0, 0)
        glRotatef(self.rot_y, 0, 1, 0)
        glTranslatef(-target[0], -target[1], -target[2])

    def handle_keys(self, keys, dt: float):
        speed = 90.0  # deg/sec
        zoom_speed = max(1.0, self.distance * 1.5)
        if keys[pygame.K_UP]:
            self.rot_x -= speed * dt
        if keys[pygame.K_DOWN]:
            self.rot_x += speed * dt
        if keys[pygame.K_LEFT]:
            self.rot_y -= speed * dt
        if keys[pygame.K_RIGHT]:
            self.rot_y += speed * dt
        if keys[pygame.K_a]:
            self.rot_z += speed * dt
        if keys[pygame.K_d]:
            self.rot_z -= speed * dt
        if keys[pygame.K_w]:
            self.distance = max(0.2, self.distance - zoom_speed * dt)
        if keys[pygame.K_s]:
            self.distance = min(1000.0, self.distance + zoom_speed * dt)

    def reset(self):
        self.rot_x, self.rot_y, self.rot_z, self.distance = (
            20.0,
            -30.0,
            0.0,
            5.0,
        )


# Utility: compute model center / size for initial framing


def compute_bounds(verts: List[Tuple[float, float, float]]):
    if not verts:
        return (0, 0, 0), 1.0
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    min_v = (min(xs), min(ys), min(zs))
    max_v = (max(xs), max(ys), max(zs))
    center = (
        (min_v[0] + max_v[0]) / 2.0,
        (min_v[1] + max_v[1]) / 2.0,
        (min_v[2] + max_v[2]) / 2.0,
    )
    size = max(max_v[0] - min_v[0], max_v[1] - min_v[1], max_v[2] - min_v[2])
    return center, size if size > 0 else 1.0


def main():
    if len(sys.argv) < 2:
        print("usage: python main.py path/to/model.obj")
        sys.exit(1)

    obj_path = sys.argv[1]
    loader = OBJLoader(obj_path)
    mesh = loader.load()

    pygame.init()
    pygame.display.set_caption("OBJ Viewer (pygame + PyOpenGL + Textures)")
    width, height = 1200, 800
    screen = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)

    setup_gl(width, height)
    set_perspective(width, height)

    # Center and scale model to a comfortable initial distance
    center, size = compute_bounds(mesh.vertices)
    cam = OrbitCamera()
    cam.distance = max(3.0, size * 2.0)

    renderer = Renderer(mesh)

    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(120) / 1000.0  # seconds
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_r:
                    cam.reset()

        keys = pygame.key.get_pressed()
        cam.handle_keys(keys, dt)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        set_perspective(width, height)
        cam.apply(center)

        # simple ground grid for orientation
        glDisable(GL_LIGHTING)
        glBegin(GL_LINES)
        glColor3f(0.2, 0.22, 0.25)
        for i in range(-10, 11):
            glVertex3f(i, 0, -10)
            glVertex3f(i, 0, 10)
            glVertex3f(-10, 0, i)
            glVertex3f(10, 0, i)
        glEnd()
        glEnable(GL_LIGHTING)

        renderer.draw()

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
