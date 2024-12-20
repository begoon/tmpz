import process from "node:process";
Bun.serve({ fetch: () => new Response("Hello World!"), port: 8000 });
console.log(await (await fetch("http://localhost:8000/")).text());
process.exit();
