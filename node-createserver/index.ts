import * as http from "node:http";

const server = http.createServer({}, (request, response) => {
    response.writeHead(200, { "Content-Type": "text/plain" });
    response.end("OK\n");
    console.dir(request);
});

server.listen(3000, () => {
    console.log("listening on https://localhost:3000");
});
