<script lang="ts">
    import Counter from "../../lib/Counter.svelte";
    import "../app.css";

    const data = window.__DATA__;
</script>

<main>
    <h1 class="fixed top-0 right-0 bg-blue-400 text-white p-2">Page 1</h1>
    <Counter />
    <a href="/">...back</a>
    <div>{JSON.stringify(data)}</div>
    <img src="/images/go.png" class="fixed bottom-0 right-0 w-[100px] hover:w-[500px]" alt="Go" />
</main>

<style>
</style>
