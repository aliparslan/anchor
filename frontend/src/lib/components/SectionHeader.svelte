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
