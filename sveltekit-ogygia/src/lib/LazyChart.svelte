<script lang="ts">
	import HydrationBadge from './HydrationBadge.svelte';

	let { values }: { values: number[] } = $props();
	let hovered = $state<number | null>(null);
	const max = $derived(Math.max(...values));
</script>

<article class="card">
	<header>
		<h3>Chart</h3>
		<HydrationBadge wake="visible" />
	</header>
	<p>
		Hydrates when it scrolls into view via <code>IntersectionObserver</code>. Hover a bar once it is
		live.
	</p>
	<svg viewBox="0 0 {values.length * 24} 100" class="chart" role="img" aria-label="Bar chart">
		{#each values as v, i}
			<rect
				role="presentation"
				x={i * 24 + 2}
				y={100 - (v / max) * 100}
				width="20"
				height={(v / max) * 100}
				fill={hovered === i ? 'var(--accent)' : 'var(--bar)'}
				onmouseenter={() => (hovered = i)}
				onmouseleave={() => (hovered = null)}
			/>
		{/each}
	</svg>
	<p class="hint">{hovered === null ? 'Hover a bar' : `Bar ${hovered + 1}: ${values[hovered]}`}</p>
</article>

<style>
	.chart {
		width: 100%;
		height: 120px;
	}
	.hint {
		min-height: 1.5em;
		color: var(--muted);
		font-size: 0.85rem;
	}
</style>
