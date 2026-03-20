<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { fetchJournal, saveJournal, fetchJournalDates } from '$lib/api';
	import { CaretLeft, CaretRight } from 'phosphor-svelte';

	let content = $state('');
	let savedIndicator = $state(false);
	let saveTimeout: ReturnType<typeof setTimeout> | null = null;
	let indicatorTimeout: ReturnType<typeof setTimeout> | null = null;
	let dates = $state<string[]>([]);
	let currentDate = $state(new Date().toISOString().split('T')[0]);
	let showPastEntries = $state(false);

	const isToday = $derived(currentDate === new Date().toISOString().split('T')[0]);

	function formatDate(iso: string): string {
		const d = new Date(iso + 'T12:00:00');
		return d.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric'
		});
	}

	function navigateDay(offset: number) {
		const d = new Date(currentDate + 'T12:00:00');
		d.setDate(d.getDate() + offset);
		currentDate = d.toISOString().split('T')[0];
		loadEntry();
	}

	async function loadEntry() {
		try {
			const entry = await fetchJournal(currentDate);
			content = entry?.content || '';
		} catch {
			content = '';
		}
	}

	function handleInput() {
		if (saveTimeout) clearTimeout(saveTimeout);
		saveTimeout = setTimeout(async () => {
			try {
				await saveJournal(currentDate, content);
				savedIndicator = true;
				if (indicatorTimeout) clearTimeout(indicatorTimeout);
				indicatorTimeout = setTimeout(() => {
					savedIndicator = false;
				}, 2000);
			} catch {}
		}, 1500);
	}

	onDestroy(() => {
		if (saveTimeout) clearTimeout(saveTimeout);
		if (indicatorTimeout) clearTimeout(indicatorTimeout);
	});

	onMount(async () => {
		await loadEntry();
		try {
			dates = await fetchJournalDates();
		} catch {}
	});
</script>

<div class="journal-card">
	<div class="journal-header">
		<div class="journal-nav">
			<button class="journal-nav-btn" onclick={() => navigateDay(-1)} aria-label="Previous day">
				<CaretLeft size={14} weight="bold" />
			</button>
			<span class="journal-date">{isToday ? 'Today' : formatDate(currentDate)}</span>
			<button class="journal-nav-btn" onclick={() => navigateDay(1)} disabled={isToday} aria-label="Next day">
				<CaretRight size={14} weight="bold" />
			</button>
		</div>
		{#if savedIndicator}
			<span class="journal-saved">Saved</span>
		{/if}
	</div>
	<textarea
		class="journal-textarea"
		bind:value={content}
		oninput={handleInput}
		placeholder={isToday ? "What's on your mind today?" : "No entry"}
		rows="4"
	></textarea>
	{#if dates.length > 1}
		<button class="journal-past-toggle" onclick={() => showPastEntries = !showPastEntries}>
			{showPastEntries ? 'Hide' : 'Recent'} entries ({dates.length})
		</button>
		{#if showPastEntries}
			<div class="journal-past-list">
				{#each dates.slice(0, 10) as d}
					<button
						class="journal-past-item"
						class:journal-past-active={d === currentDate}
						onclick={() => { currentDate = d; loadEntry(); showPastEntries = false; }}
					>
						{new Date(d + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
					</button>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
	.journal-past-toggle {
		display: block;
		width: 100%;
		padding: 8px;
		margin-top: 8px;
		border: none;
		border-top: 1px solid var(--border);
		background: none;
		color: var(--text-tertiary);
		font-family: var(--font-mono);
		font-size: 11px;
		cursor: pointer;
		transition: color 0.15s ease;
	}

	.journal-past-toggle:hover {
		color: var(--text-secondary);
	}

	.journal-past-list {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		padding-top: 8px;
	}

	.journal-past-item {
		padding: 4px 10px;
		border-radius: 14px;
		border: 1px solid var(--border);
		background: none;
		color: var(--text-secondary);
		font-family: var(--font-mono);
		font-size: 11px;
		cursor: pointer;
		transition: all 0.15s ease;
	}

	.journal-past-item:hover {
		border-color: var(--text-tertiary);
		color: var(--text);
	}

	.journal-past-active {
		background: var(--accent);
		border-color: var(--accent);
		color: var(--bg);
	}
</style>
