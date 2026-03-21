<script lang="ts">
	import { theme, toggleTheme } from '$lib/theme';
	import { getScore, onScoreChange, refreshScore } from '$lib/score';
	import type { DailyScore } from '$lib/api';
	import ShutdownModal from './ShutdownModal.svelte';
	import { Moon, Sun } from 'phosphor-svelte';

	let { title }: { title: string } = $props();

	let dailyScore = $state<DailyScore | null>(getScore());
	$effect(() => { return onScoreChange((s) => dailyScore = s); });
	let showShutdown = $state(false);
</script>

<div class="page-header">
	<h1 class="greeting">{title}</h1>
	<div class="page-header-actions">
		{#if dailyScore !== null}
			<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
			<div class="score-ring" title="{dailyScore.score}/100 — tap for details" onclick={() => showShutdown = true} style="cursor: pointer">
				<svg viewBox="0 0 36 36" class="score-ring-svg">
					<circle cx="18" cy="18" r="15.5" fill="none" stroke="var(--border)" stroke-width="3" />
					<circle cx="18" cy="18" r="15.5" fill="none" stroke="var(--accent)" stroke-width="3"
						stroke-dasharray="{dailyScore.score * 0.9749} {97.49 - dailyScore.score * 0.9749}"
						stroke-dashoffset="0" stroke-linecap="round" />
				</svg>
				<span class="score-ring-text">{dailyScore.score}</span>
			</div>
		{/if}
		<button class="theme-toggle" onclick={toggleTheme} aria-label="Toggle theme">
			{#if $theme === 'light'}
				<Moon size={18} weight="duotone" />
			{:else}
				<Sun size={18} weight="duotone" />
			{/if}
		</button>
	</div>
</div>

<ShutdownModal open={showShutdown} onclose={() => { showShutdown = false; refreshScore(); }} />
