<script>
    let { children } = $props();
    import "../app.css";
</script>

<div class="flex flex-col items-center justify-center h-screen">
    {@render children()}
</div>
