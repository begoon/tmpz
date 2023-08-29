const ws = new WebSocket("wss://ws-chatter.deno.dev");
function shell() {
    const message = prompt("@ ");
    if (message === ".exit") {
        ws.close();
        Deno.exit(0);
    }
    console.log("sending [", message, "]");
    ws.send(message ?? "");
    setTimeout(shell, 100);
}
ws.onopen = () => {
    ws.send("hello, world!");
    ws.send("ping");
    setTimeout(shell, 1);
};
ws.onclose = (e) => {
    console.log("disconnected", e.code, e.reason);
    Deno.exit(0);
};
ws.onmessage = (event) => {
    console.log("response", event.data);
};
