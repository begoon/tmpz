<script lang="ts">
    import { page } from "$app/state";
</script>

ABC: {page.data.message}

{#await page.data.after.lazy}
    <p>...</p>
{:then value}
    <p>lazy value: {value}</p>
{/await}

{#await page.data.after.coala}
    <p>***</p>
{:then coala}
    <p>coala: {coala}</p>
{/await}
