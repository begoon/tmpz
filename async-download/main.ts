const size = 10;
const link = `http://ipv4.download.thinkbroadband.com/${size}MB.zip`;
const N = 10;

type Downloaded = { n: number; sz: number };

async function download_file(url: string, n: number) {
    console.log(`downloading ${url}`);
    if (Math.random() < 0.1) throw new Error(`random error: n=${n}`);
    await new Promise((resolve) => setTimeout(resolve, 1000 * Math.random()));
    const sz = (await (await fetch(url)).arrayBuffer()).byteLength;
    console.log(`${n}: downloaded ${url}, ${sz} bytes`);
    const expected = size * 1024 * 1024;
    if (sz !== expected)
        throw new Error(`unexpected size ${sz}, expected ${expected}`);
    return { n, sz };
}

async function main() {
    const started = performance.now();
    const tasks = new Array(N).fill(0).map((_, i) => download_file(link, i));
    const sizes = await Promise.allSettled(tasks);
    console.log(sizes);
    const total =
        sizes
            .filter((s) => s.status === "fulfilled")
            .map((s) => (s as PromiseFulfilledResult<Downloaded>).value)
            .reduce((a, b) => a + b.sz, 0) /
        1024 /
        1024;
    const elapsed = (performance.now() - started) / 1000;
    console.log(`${N} files downloaded in ${elapsed.toFixed()} seconds`);
    console.log(`throughput: ${(total / elapsed).toFixed(2)} MB/s`);
}

main();
