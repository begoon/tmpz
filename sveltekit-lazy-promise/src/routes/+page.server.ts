export async function load() {
    return {
        message: "MESSAGE",
        after: {
            lazy: new Promise((resolve) => {
                setTimeout(() => {
                    resolve("LAZY VALUE");
                }, 2000);
            }),
            coala: new Promise((resolve) => {
                setTimeout(() => {
                    resolve("COALA VALUE");
                }, 5000);
            }),
        },
    };
}
