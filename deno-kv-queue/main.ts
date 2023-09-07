const kv = await Deno.openKv();

let n = 0;

kv.listenQueue(async (msg: unknown) => {
    console.log("RECEIVED", msg);
    const delta = Date.now() - new Date(msg.value["when"]).getTime();
    console.log("DELTA", delta);
});

setInterval(async () => {
    const value = { when: new Date().toISOString(), n };
    console.log("PUBLISHING", value);
    await kv.enqueue({ key: ["msg"], value }, { delay: 1000 });
    n += 1;
}, 3000);
