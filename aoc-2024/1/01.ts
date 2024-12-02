import fs from "node:fs";

const data = fs
    .readFileSync("in.txt", "utf8")
    .split("\n")
    .filter((s) => s)
    .map((s) => s.split("   "))
    .map(([a, b]) => [Number(a), Number(b)]);

const a = data.map(([a, _]) => a).toSorted();
const b = data.map(([_, b]) => b).toSorted();

const dist = a.map((_, i) => Math.abs(a[i] - b[i]));
const min = dist.reduce((a, x) => a + x, 0);

console.log(min);

const count_b: { [n: number]: number } = {};
b.forEach((n) => (count_b[n] = (count_b[n] || 0) + 1));

const aa = a.map((v) => v * (count_b[v] || 0));

console.log(aa.reduce((a, x) => a + x, 0));
