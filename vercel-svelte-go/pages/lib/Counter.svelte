<script lang="ts">
    let count: number = $state(0);

    const increment = () => {
        count += 1;
        const id = new Date().getTime();
        fetch(`/endpoint/click/${id}`);
    };
</script>

<button onclick={increment} class="px-4 py-2 font-bold text-white bg-blue-500 rounded hover:bg-blue-700">
    count is {count}
</button>
