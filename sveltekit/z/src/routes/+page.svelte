<script>
    const loader = async () => {
        const v = await (
            await fetch("/api?abc=Z?z=10", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ x: 1, v: 0 }),
            })
        ).json();
        console.log(v);
        return v;
    };
    let data = loader();
</script>

<h1>Welcome to SvelteKit</h1>
<p>
    Visit <a href="https://kit.svelte.dev">kit.svelte.dev</a> to read the documentation
</p>
{#await data}
    <p>...loading</p>
{:then data}
    <pre>{JSON.stringify(data, null, "  ")}</pre>
{:catch error}
    <p style="color: red">{error.message}</p>
{/await}
