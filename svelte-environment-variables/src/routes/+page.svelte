<script ts="ts">
    import { env as dynamic_public_env } from "$env/dynamic/public";
    import { VAR_STATIC_PUBLIC } from "$env/static/public";

    export let data;
</script>

<h1>$env/dynamic/public</h1>
<pre>{JSON.stringify(dynamic_public_env.VAR_DYNAMIC_PUBLIC, null, 2)}</pre>

<h1>$env/static/public</h1>
<pre>{JSON.stringify(VAR_STATIC_PUBLIC, null, 2)}</pre>

<h1>server</h1>

<pre>{JSON.stringify(data, null, 2)}</pre>
