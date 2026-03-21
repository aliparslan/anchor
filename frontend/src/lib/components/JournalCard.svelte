<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { fetchJournal, saveJournal, fetchJournalDates, fetchJournalEntries, type JournalPreview } from '$lib/api';
	import { CaretLeft, CaretRight } from 'phosphor-svelte';

	let content = $state('');
	let savedIndicator = $state(false);
	let saveTimeout: ReturnType<typeof setTimeout> | null = null;
	let indicatorTimeout: ReturnType<typeof setTimeout> | null = null;
	let totalEntries = $state(0);
	let entryDatesSet = $state<Set<string>>(new Set());
	let currentDate = $state(new Date().toISOString().split('T')[0]);
	let showAllEntries = $state(false);
	let allEntries = $state<JournalPreview[]>([]);
	let hasMoreEntries = $state(true);
	let loadingMore = $state(false);
	let dateInputEl: HTMLInputElement;

	const PAGE_SIZE = 20;

	const isToday = $derived(currentDate === new Date().toISOString().split('T')[0]);
	const wordCount = $derived(content.trim() ? content.trim().split(/\s+/).length : 0);

	const prompts = [
		"What made you smile today?",
		"What's one thing you'd tell your yesterday self?",
		"What are you avoiding right now?",
		"Describe your energy level in one sentence.",
		"What's something small that went well?",
		"What would make tomorrow great?",
		"What's taking up the most mental space?",
		"Write about a conversation you had today.",
		"What are you grateful for right now?",
		"If today had a title, what would it be?",
		"What surprised you today?",
		"What's something you learned recently?",
		"How did you take care of yourself today?",
		"What's a decision you're sitting on?",
		"Describe your mood without using emotion words.",
		"What's one thing you want to let go of?",
		"What did you spend the most time on today?",
		"Write about something you're looking forward to.",
		"What boundary did you set or need to set?",
		"What's something you did for the first time recently?",
		"How are you different from a year ago?",
		"What's your body telling you right now?",
		"What would you do if you had no obligations today?",
		"Write about a moment of quiet today.",
		"What's a pattern you've noticed in yourself?",
		"Who made a difference in your day?",
		"What are you overthinking?",
		"What felt hard today and why?",
		"What's something you're proud of this week?",
		"Describe a place you'd rather be right now.",
		"What's a question you keep coming back to?",
		"What did you eat today and how did it make you feel?",
		"Write about something that's changing in your life.",
		"What's one thing you want to remember about today?",
		"What permission do you need to give yourself?",
		"What's your relationship with rest right now?",
		"Describe today in exactly three words.",
		"What did you create or contribute today?",
		"What's weighing on you that you haven't said out loud?",
		"If you could redo one moment today, which would it be?"
	];

	function getDailyPrompt(dateStr: string): string {
		let hash = 0;
		for (let i = 0; i < dateStr.length; i++) {
			hash = ((hash << 5) - hash) + dateStr.charCodeAt(i);
			hash |= 0;
		}
		return prompts[Math.abs(hash) % prompts.length];
	}

	function getDotDays(): { date: string; hasEntry: boolean; isToday: boolean; isSelected: boolean }[] {
		const todayStr = new Date().toISOString().split('T')[0];
		const today = new Date(todayStr + 'T12:00:00');
		const selected = new Date(currentDate + 'T12:00:00');

		const endCandidate = new Date(selected);
		endCandidate.setDate(endCandidate.getDate() + 3);
		const end = endCandidate > today ? today : endCandidate;
		const start = new Date(end);
		start.setDate(start.getDate() - 6);

		const days = [];
		for (let i = 0; i < 7; i++) {
			const d = new Date(start);
			d.setDate(d.getDate() + i);
			const iso = d.toISOString().split('T')[0];
			days.push({
				date: iso,
				hasEntry: entryDatesSet.has(iso),
				isToday: iso === todayStr,
				isSelected: iso === currentDate
			});
		}
		return days;
	}

	const dotDays = $derived(getDotDays());

	function navigateDay(offset: number) {
		const d = new Date(currentDate + 'T12:00:00');
		d.setDate(d.getDate() + offset);
		const today = new Date().toISOString().split('T')[0];
		const iso = d.toISOString().split('T')[0];
		if (iso > today) return;
		selectDate(iso);
	}

	function openDatePicker() {
		if (dateInputEl) {
			dateInputEl.value = currentDate;
			dateInputEl.focus();
			dateInputEl.click();
		}
	}

	function handleDatePick(e: Event) {
		const val = (e.target as HTMLInputElement).value;
		if (!val) return;
		const today = new Date().toISOString().split('T')[0];
		if (val > today) return;
		selectDate(val);
	}

	async function loadEntry() {
		try {
			const entry = await fetchJournal(currentDate);
			content = entry?.content || '';
		} catch {
			content = '';
		}
	}

	function selectDate(date: string) {
		if (date === currentDate) return;
		currentDate = date;
		loadEntry();
	}

	async function toggleAllEntries() {
		if (showAllEntries) {
			showAllEntries = false;
		} else {
			if (allEntries.length === 0) {
				const entries = await fetchJournalEntries(PAGE_SIZE, 0);
				allEntries = entries;
				hasMoreEntries = entries.length >= PAGE_SIZE;
			}
			showAllEntries = true;
		}
	}

	async function loadMoreEntries() {
		if (loadingMore || !hasMoreEntries) return;
		loadingMore = true;
		const entries = await fetchJournalEntries(PAGE_SIZE, allEntries.length);
		allEntries = [...allEntries, ...entries];
		hasMoreEntries = entries.length >= PAGE_SIZE;
		loadingMore = false;
	}

	function formatEntryDate(iso: string): string {
		const d = new Date(iso + 'T12:00:00');
		return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	function formatDateLabel(dateStr: string): string {
		if (dateStr === new Date().toISOString().split('T')[0]) return 'Today';
		return new Date(dateStr + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
	}

	function handleInput() {
		if (saveTimeout) clearTimeout(saveTimeout);
		saveTimeout = setTimeout(async () => {
			try {
				await saveJournal(currentDate, content);
				entryDatesSet = new Set([...entryDatesSet, currentDate]);
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
			const dates = await fetchJournalDates();
			totalEntries = dates.length;
			entryDatesSet = new Set(dates);
		} catch {}
	});
</script>

<div class="jrnl-card">
	<input
		type="date"
		class="jrnl-date-input-hidden"
		bind:this={dateInputEl}
		onchange={handleDatePick}
		max={new Date().toISOString().split('T')[0]}
	/>

	<div class="jrnl-header">
		<button class="jrnl-nav-arrow" onclick={() => navigateDay(-1)} aria-label="Previous day">
			<CaretLeft size={12} weight="bold" />
		</button>
		<button class="jrnl-date-label" onclick={openDatePicker}>
			{formatDateLabel(currentDate)}
			{#if savedIndicator}
				<span class="jrnl-saved-dot"></span>
			{/if}
		</button>
		<button class="jrnl-nav-arrow" onclick={() => navigateDay(1)} aria-label="Next day" disabled={isToday}>
			<CaretRight size={12} weight="bold" />
		</button>
	</div>

	<div class="jrnl-body">
		<textarea
			class="jrnl-textarea"
			bind:value={content}
			oninput={handleInput}
			placeholder={getDailyPrompt(currentDate)}
		></textarea>
	</div>

	<div class="jrnl-footer">
		<div class="jrnl-dots">
			{#each dotDays as day}
				<span
					class="jrnl-dot"
					class:jrnl-dot-filled={day.hasEntry && !day.isSelected}
					class:jrnl-dot-selected={day.isSelected}
					class:jrnl-dot-empty={!day.hasEntry && !day.isSelected}
				></span>
			{/each}
		</div>
		<span class="jrnl-wordcount">{wordCount} {wordCount === 1 ? 'word' : 'words'}</span>
		<button class="jrnl-entries-toggle" onclick={toggleAllEntries}>
			{showAllEntries ? 'Hide' : `${totalEntries} entries`}
		</button>
	</div>

	<div
		class="jrnl-entries-drawer"
		class:jrnl-entries-drawer-open={showAllEntries}
	>
		<div class="jrnl-entries-list">
			{#each allEntries as entry}
				<button
					class="jrnl-entry-row"
					class:jrnl-entry-active={entry.date === currentDate}
					onclick={() => selectDate(entry.date)}
				>
					<span class="jrnl-entry-date">{formatEntryDate(entry.date)}</span>
					<span class="jrnl-entry-preview">{entry.preview}</span>
				</button>
			{/each}
			{#if hasMoreEntries && allEntries.length > 0}
				<button class="jrnl-load-more" onclick={loadMoreEntries} disabled={loadingMore}>
					{loadingMore ? 'Loading...' : 'Load more'}
				</button>
			{/if}
			{#if allEntries.length === 0}
				<span class="jrnl-entries-empty">No entries yet</span>
			{/if}
		</div>
	</div>
</div>
