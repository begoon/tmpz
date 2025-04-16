export async function load({ fetch }) {
    const { ip } = await (await fetch("https://api.ipify.org?format=json")).json();
    console.log({ ip });
    //
    const started = performance.now();
    const httpbin = fetch("https://httpbin.org/delay/1");
    const elapsed = ((performance.now() - started) / 1000).toFixed(2);
    console.log({ elapsed, httpbin });
    //
    return { title: "about us", ip, httpbin, elapsed };
}
