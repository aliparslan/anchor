<script lang="ts">
	import type { Snippet } from 'svelte';
	let { title, class: className, style, children }: {
		title: string;
		class?: string;
		style?: string;
		children?: Snippet;
	} = $props();
</script>

<div class="section-header {className ?? ''}" style={style}>
	<span class="section-title">{title}</span>
	{#if children}
		{@render children()}
	{/if}
</div>

<style>
.section-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: var(--space-md);
}

.section-title {
	font-family: var(--font-display);
	font-size: 12px;
	font-weight: 600;
	text-transform: uppercase;
	letter-spacing: 0.08em;
	color: var(--text);
}
</style>
