<script lang="ts">
	import HydrationBadge from './HydrationBadge.svelte';

	let open = $state(false);
</script>

<article class="card">
	<header>
		<h3>Accordion</h3>
		<HydrationBadge wake="interaction" />
	</header>
	<p>
		Ships no JS until you first interact with it. The first click both loads the island and replays
		the event.
	</p>
	<button onclick={() => (open = !open)} aria-expanded={open}>
		{open ? 'Hide' : 'Show'} details
	</button>
	{#if open}
		<p class="details">
			This content toggled in the browser, so the island is now hydrated. Before your click the button
			was inert server HTML.
		</p>
	{/if}
</article>

<style>
	.details {
		margin-top: 0.75rem;
		padding: 0.75rem;
		border-left: 3px solid var(--accent);
		background: var(--code-bg);
	}
</style>
