const BACKGROUND = "#101010";
const FOREGROUND = "#50FF50";

console.log(game);
game.width = 800;
game.height = 800;
const ctx = game.getContext("2d");
console.log(ctx);

function clear() {
    ctx.fillStyle = BACKGROUND;
    ctx.fillRect(0, 0, game.width, game.height);
}

function point({ x, y }) {
    const s = 20;
    ctx.fillStyle = FOREGROUND;
    ctx.fillRect(x - s / 2, y - s / 2, s, s);
}

function line(p1, p2) {
    ctx.lineWidth = 3;
    ctx.strokeStyle = FOREGROUND;
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.stroke();
}

function screen(p) {
    // -1..1 => 0..2 => 0..1 => 0..w
    return {
        x: ((p.x + 1) / 2) * game.width,
        y: (1 - (p.y + 1) / 2) * game.height,
    };
}

function project({ x, y, z }) {
    return {
        x: x / z,
        y: y / z,
    };
}

const FPS = 60;

function translate_z({ x, y, z }, dz) {
    return { x, y, z: z + dz };
}

function rotate_xz({ x, y, z }, angle) {
    const c = Math.cos(angle);
    const s = Math.sin(angle);
    return {
        x: x * c - z * s,
        y,
        z: x * s + z * c,
    };
}

let dz = 1;
let angle = 0;

function sub(a, b) {
    return { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z };
}

function dot(a, b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

function cross(a, b) {
    return {
        x: a.y * b.z - a.z * b.y,
        y: a.z * b.x - a.x * b.z,
        z: a.x * b.y - a.y * b.x,
    };
}

// returns true if the face should be drawn (front-facing + in front of camera)
function face_visible(face, tvs) {
    // need at least a triangle to define a plane
    if (face.length < 3) return true;

    const a = tvs[face[0]];
    const b = tvs[face[1]];
    const c = tvs[face[2]];

    // if any vertex is behind/at the camera, skip (prevents x/z blow-ups)
    const EPS = 1e-3;
    for (const idx of face) {
        if (tvs[idx].z <= EPS) return false;
    }

    // normal from winding order
    const n = cross(sub(b, a), sub(c, a));

    // Camera at origin. Face is visible if its normal points towards the camera.
    // This test is stable even if the face is not centered:
    // front-facing if dot(n, a) < 0 (with your projection assuming +z forward).
    return dot(n, a) < 0;
}

function frame() {
    const dt = 1 / FPS;
    angle += Math.PI * dt;
    clear();

    // Transform vertices once per frame (camera space)
    const translated_vs = vs.map((v) => translate_z(rotate_xz(v, angle), dz));

    for (const f of fs) {
        if (!face_visible(f, translated_vs)) continue;

        for (let i = 0; i < f.length; ++i) {
            const a = translated_vs[f[i]];
            const b = translated_vs[f[(i + 1) % f.length]];

            line(screen(project(a)), screen(project(b)));
        }
    }

    setTimeout(frame, 1000 / FPS);
}
setTimeout(frame, 1000 / FPS);
