export class Bus {
    constructor() {
        this.subscriptions = {};
    }

    on = (event, callback) => {
        if (!this.subscriptions[event]) this.subscriptions[event] = [];
        this.subscriptions[event].push(callback);
    };

    emit = (event, ...args) => {
        if (!this.subscriptions[event]) return;
        console.dir(`emitted [${event}]`, args ? `with: ${args}` : "");
        const callbacks = this.subscriptions[event];
        if (!callbacks || callbacks.length === 0) {
            console.error(`unhandled event: ${event}`);
            return;
        }
        callbacks.forEach((callback) => callback(...args));
    };
}
