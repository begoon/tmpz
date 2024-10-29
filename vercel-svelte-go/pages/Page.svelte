<script lang="ts">
    import "./app.css";
    import Counter from "./lib/Counter.svelte";

    // @ts-ignore
    const data = window.__DATA__;
</script>

<h1 class="text-5xl">[root page]</h1>
<Counter />
{JSON.stringify(data, null, 2)}

<ul>
    <li><a class="underline" href="a">page a</a></li>
    <li><a class="underline" href="b">page b</a></li>
</ul>
