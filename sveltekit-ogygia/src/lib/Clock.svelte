<script lang="ts">
	import HydrationBadge from './HydrationBadge.svelte';

	// Rendered on the server with the server's time, then takes over ticking once hydrated.
	let { initial }: { initial: string } = $props();
	// svelte-ignore state_referenced_locally -- the server time is only the seed
	let now = $state(initial);

	$effect(() => {
		const id = setInterval(() => {
			now = new Date().toLocaleTimeString(undefined, { hour12: false });
		}, 1000);
		return () => clearInterval(id);
	});
</script>

<article class="card">
	<header>
		<h3>Clock</h3>
		<HydrationBadge wake="idle" />
	</header>
	<p>Hydrates in <code>requestIdleCallback</code>, after the browser finishes the urgent work.</p>
	<output class="clock">{now}</output>
</article>

<style>
	.clock {
		font-size: 2rem;
		font-variant-numeric: tabular-nums;
		font-weight: 600;
	}
</style>
