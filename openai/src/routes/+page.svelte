<script lang="ts">
    let model = $state("dall-e-3");
    let query = $state("");

    let working = $state(false);
    let image = $state("");

    async function create() {
        if (working) return;
        working = true;
        const response = await fetch("/image", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model, query }),
        });
        const data = await response.json();
        console.log(data);
        image = data.image;
        working = false;
    }
</script>

<h1 class="uppercase pb-2">chat-gpt | model {model}</h1>

<select bind:value={model} class="border border-gray-300 rounded-md">
    <option value="dall-e-3" selected>DALL·E 3</option>
    <option value="dall-e-2">DALL·E 2</option>
</select>

<textarea
    class="border border-gray-300 rounded-md w-full h-40"
    bind:value={query}
></textarea>
<button
    class="bg-blue-500 text-white px-4 py-2 rounded-md"
    onclick={create}
    disabled={working}
>
    {working ? "working..." : "create"}
</button>

{#if image}
    <!-- svelte-ignore a11y_img_redundant_alt -->
    <img src={image} alt="image" class="mt-4" />
{/if}
