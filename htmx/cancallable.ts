async function withTimeout<T>(f: () => Promise<T>, timeout: number) {
    let timer;
    const bearer = new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error("timeout")), timeout);
    });

    try {
        return await Promise.race([f(), bearer]);
    } finally {
        if (timer !== undefined) clearTimeout(timer);
    }
}

function longFunction() {
    console.log("long function started");
    return new Promise((resolve) => {
        setTimeout(() => {
            console.log("long function done");
            resolve("done");
        }, 500);
    });
}

console.log(await withTimeout(longFunction, 100));
