<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchJournal, saveJournal, fetchJournalDates } from '$lib/api';

	let content = $state('');
	let savedIndicator = $state(false);
	let saveTimeout: ReturnType<typeof setTimeout> | null = null;
	let indicatorTimeout: ReturnType<typeof setTimeout> | null = null;
	let dates = $state<string[]>([]);
	let currentDate = $state(new Date().toISOString().split('T')[0]);

	const isToday = $derived(currentDate === new Date().toISOString().split('T')[0]);

	function formatDate(iso: string): string {
		const d = new Date(iso + 'T12:00:00');
		return d.toLocaleDateString('en-US', {
			weekday: 'long',
			month: 'long',
			day: 'numeric',
			year: 'numeric'
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

	onMount(async () => {
		await loadEntry();
		try {
			dates = await fetchJournalDates();
		} catch {}
	});
</script>

<div class="journal-card">
	<div class="journal-header">
		<span class="section-title">Journal</span>
		<div class="journal-nav">
			<button class="journal-nav-btn" onclick={() => navigateDay(-1)} aria-label="Previous day">
				<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
			</button>
			<span class="journal-date">{isToday ? 'Today' : formatDate(currentDate)}</span>
			<button class="journal-nav-btn" onclick={() => navigateDay(1)} disabled={isToday} aria-label="Next day">
				<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
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
		placeholder={isToday ? "What's on your mind today?" : "No entry for this day"}
		rows="4"
	></textarea>
</div>
