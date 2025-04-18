<script>
    import Spinner from "./Spinner.svelte";

    console.clear();

    let { data } = $props();
    console.log("data", data);

    let { title, elapsed: preload, ip, httpbin } = data;

    let loadded = $state("");

    let started = $state(performance.now());
    let elapsed = $state(0);

    httpbin
        .then((data) => {
            console.log("httpbin", data);
            loadded = data.url;
            elapsed = (performance.now() - started) / 1000;
            console.log({ elapsed });
        })
        .catch((error) => {
            console.error("httpbin error", error);
            loadded = "error";
        });
</script>

<div>{title} | {preload}: {ip}</div>
<div>
    {#if elapsed}
        loaded:
        <span class="text-green-500">
            <a href={loadded} target="_blank" class="underline">{loadded}</a>
        </span>
        in {elapsed.toFixed(2)}s
    {:else}
        <Spinner />
    {/if}
</div>
<a href="#/" class="underline">home</a>
