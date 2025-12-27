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

// --- wave controls ---
const WAVE_AMP_X = 0.12; // horizontal amplitude (world units)
const WAVE_AMP_Y = 0.12; // vertical amplitude (world units)
const WAVE_FREQ_X = 3.0; // how many "wiggles" across X
const WAVE_FREQ_Y = 3.0; // how many "wiggles" across Y
const WAVE_SPEED = 2.0; // animation speed

// Keep an immutable copy of original vertices
const original_vertices = vs.map((v) => ({ ...v }));

function wavedVertex(v, t) {
    // Phase varies per-vertex based on position
    // (proportional to its X/Y, creating the traveling-wave feel).
    const phase = t * WAVE_SPEED + v.x * WAVE_FREQ_X + v.y * WAVE_FREQ_Y;

    return {
        x: v.x + Math.sin(phase) * WAVE_AMP_X,
        y: v.y + Math.cos(phase) * WAVE_AMP_Y,
        z: v.z, // keep z as-is (we can also wave z if we want)
    };
}

let dz = 1;
let angle = 0;
let t = 0;

function frame() {
    const dt = 1 / FPS;
    angle += Math.PI * dt;
    t += dt;

    clear();

    // Build waved vertices for this frame
    const waved_vertices = original_vertices.map((v) => wavedVertex(v, t));

    for (const f of fs) {
        for (let i = 0; i < f.length; ++i) {
            const a = waved_vertices[f[i]];
            const b = waved_vertices[f[(i + 1) % f.length]];
            line(
                screen(project(translate_z(rotate_xz(a, angle), dz))),
                screen(project(translate_z(rotate_xz(b, angle), dz)))
            );
        }
    }
    setTimeout(frame, 1000 / FPS);
}
setTimeout(frame, 1000 / FPS);
