const html = (endpoint: string) => `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RPi</title>
</head>
<body>
    <div id="device"></div>
    <div id="message"></div>
    <input id="period" type="number" min="100" max="1000" value="200">
    <button onclick="led()">LED</button>

    <script>
        const device = document.getElementById('device');
        const message = document.getElementById('message');
        const period = document.getElementById('period');

        const ws = new WebSocket('wss://${endpoint}/monitor');

        ws.onopen = () => console.log('connected');

        ws.onmessage = (event) => {
            const data = event.data;
            if (data.startsWith("/device")) {
                device.textContent = data;
                console.log(data);
            } else {
                message.textContent = data;
            }
        };

        function led() {
            console.log("led", period.value);
            ws.send("/led " + period.value);
        }

        ws.onerror = (error) => console.error(error);
        ws.onclose = (event) => console.log('closed');
    </script>
</body>
</html>`;

let period = 100;

let message: string | undefined = undefined;
let device: string | undefined = undefined;

Deno.serve({}, (req) => {
    const url = new URL(req.url);
    if (req.headers.get("upgrade") != "websocket") {
        const body = new TextEncoder().encode(html(url.host));
        return new Response(body);
    }
    if (url.pathname == "/monitor") {
        const { socket, response } = Deno.upgradeWebSocket(req);
        socket.addEventListener("open", async () => {
            console.log("monitor connected", socket.readyState);
            while (socket.readyState == WebSocket.OPEN) {
                if (device) {
                    socket.send("/device " + device);
                    device = undefined;
                }
                if (message) {
                    socket.send(message);
                    message = undefined;
                } else {
                    await new Promise((resolve) => setTimeout(resolve, 100));
                }
            }
        });
        socket.addEventListener("close", (e) => {
            console.log("monitor disconnected", e.code, e.reason);
        });
        socket.addEventListener("message", (event) => {
            const { data } = event;
            if (data == "/exit") period = 0;
            if (data.startsWith("/led")) {
                period = data.split(" ")[1];
                console.log("/led", period);
            }
        });
        return response;
    }
    const { socket, response } = Deno.upgradeWebSocket(req);
    socket.addEventListener("open", () => {
        console.log("client connected");
    });
    socket.addEventListener("close", (e) => {
        console.log("client disconnected", e.code, e.reason);
    });
    socket.addEventListener("message", (event) => {
        false && console.log("message", event.data);
        if (event.data === "/ping") {
            socket.send("/pong");
        } else if (event.data.startsWith("/device")) {
            device = event.data.split(" ").slice(1).join(" ");
        } else if (event.data.startsWith("/led")) {
            period = event.data.split(" ")[1];
        } else if (event.data === "/bye") {
            socket.close(1000, "bye!");
        } else {
            message = event.data;
            try {
                socket.send(message + " " + period);
            } catch (e) {
                socket.send(e.toString());
            }
        }
    });
    return response;
});
