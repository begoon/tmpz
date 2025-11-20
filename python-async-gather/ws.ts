const socket = new WebSocket("ws://localhost:8000/ws");

socket.onopen = async () => {
    console.log("websocket connection established");
    let i = 1;
    while (socket.readyState === WebSocket.OPEN) {
        console.log("SEND", i);
        socket.send(i.toString());
        await new Promise((resolve) => setTimeout(resolve, 30));
        i += 1;
    }
};

socket.onmessage = (event) => {
    console.log("RECV", event.data);
};

socket.onclose = () => {
    console.log("websocket connection closed");
};

socket.onerror = (error) => {
    console.error("websocket error:", error);
};
