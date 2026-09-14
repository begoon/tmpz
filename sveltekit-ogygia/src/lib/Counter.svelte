<script lang="ts">
	import HydrationBadge from './HydrationBadge.svelte';

	let { start = 0 }: { start?: number } = $props();
	// svelte-ignore state_referenced_locally -- `start` is deliberately only the initial value
	let count = $state(start);
</script>

<article class="card">
	<header>
		<h3>Counter</h3>
		<HydrationBadge wake="load" />
	</header>
	<p>Hydrates immediately. Use this for above-the-fold UI that must respond on first paint.</p>
	<div class="row">
		<button onclick={() => count--}>−</button>
		<output>{count}</output>
		<button onclick={() => count++}>+</button>
	</div>
</article>
