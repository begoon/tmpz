Deno.serve({ port: 8000, onListen: () => {} }, () => new Response("Hello World!"));
console.log(await(await fetch("http://localhost:8000/")).text());
Deno.exit();
