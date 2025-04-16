<script>
    import { version } from "$app/environment";
    let counter = $state(0);
</script>

<p>counter: {counter}</p>
<p>version: {version}</p>
<span>
    <button class="bg-blue-500 text-white px-4 py-2 rounded cursor-pointer" onclick={() => counter++}>+</button>
    <button class="bg-red-500 text-white px-4 py-2 rounded cursor-pointer" onclick={() => counter--}>-</button>
</span>
<a href="#/about" class="mt-4 text-blue-500 hover:underline">about</a>
