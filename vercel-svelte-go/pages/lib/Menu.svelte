<script lang="ts">
</script>

{#snippet link(href: string, text: string)}
    <li class="px-4 text-white hover:underline bg-slate-600">
        <a href="{href}">{text}</a>
    </li>
{/snippet}
<menu class="flex items-start w-full space-x-2 bg-slate-400">
    {@render link("/", "/")}
    {@render link("/a/ABC", "a")}
    {@render link("/b","b")}
    {@render link("/cms","cms")}
    {@render link("/z","Z")}
</menu>
