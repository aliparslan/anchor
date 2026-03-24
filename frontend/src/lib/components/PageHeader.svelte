<script lang="ts">
	import { theme, toggleTheme } from '$lib/theme';
	import { getScore, onScoreChange, refreshScore } from '$lib/score';
	import type { DailyScore } from '$lib/api';
	import ShutdownModal from './ShutdownModal.svelte';
	import { Moon, Sun, GearSix } from 'phosphor-svelte';

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
		<a href="/settings" class="theme-toggle" aria-label="Settings">
			<GearSix size={18} weight="duotone" />
		</a>
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

<style>
.page-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: var(--space-widget);
}

.greeting {
	font-family: var(--font-display);
	font-size: 32px;
	font-weight: 600;
	letter-spacing: -0.02em;
}

.page-header-actions {
	display: flex;
	align-items: center;
	gap: var(--space-sm);
}

.theme-toggle {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 36px;
	height: 36px;
	border-radius: var(--radius-full);
	border: 1px solid var(--border);
	background: none;
	color: var(--text-tertiary);
	cursor: pointer;
	transition: all var(--ease-micro);
	flex-shrink: 0;
	text-decoration: none;
}

.theme-toggle:hover {
	background: var(--bg-hover);
	color: var(--text);
	border-color: var(--text-tertiary);
}

.theme-toggle:active {
	transform: scale(0.9);
}

.score-ring {
	position: relative;
	width: 36px;
	height: 36px;
	flex-shrink: 0;
}

.score-ring-svg {
	width: 100%;
	height: 100%;
	transform: rotate(-90deg);
}

.score-ring-text {
	position: absolute;
	inset: 0;
	display: flex;
	align-items: center;
	justify-content: center;
	font-family: var(--font-mono);
	font-size: 10px;
	font-weight: 500;
	color: var(--text);
}

@media (max-width: 600px) {
	.greeting {
		font-size: 26px;
	}
}
</style>
