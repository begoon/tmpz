<script lang="ts">
    let n: number = 1;
    let s: string;
    $: s = n.toString();
    function f(a: boolean): string {
        return "f(): " + a;
    }
</script>

<div class="text-8xl">I'm ROOT!!!</div>
<div class="text-8xl">n = {n}</div>
<div class="text-8xl">s = {s}</div>
<div class="text-8xl">f() = {f(false)}</div>
