<script lang="ts">
    import Counter from "../lib/Counter.svelte";
    import JSONer from "../lib/JSONer.svelte";

    // @ts-ignore
    const data = window.__DATA__;
</script>

<h1 class="text-5xl">[PAGE BBB]</h1>
<Counter />

<JSONer value={data} />
