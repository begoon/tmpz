<script lang="ts">
    let count: number = $state(0);

    const increment = () => {
        count += 1;
    };
</script>

<button onclick={increment} class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
    count is {count}
</button>
