<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { fetchJournal, saveJournal, fetchJournalDates, fetchJournalEntries, type JournalPreview } from '$lib/api';
	import { CaretLeft, CaretRight } from 'phosphor-svelte';
	import { localDate } from '$lib/utils';
	import { createAutoSave } from '$lib/autoSave.svelte';

	let content = $state('');
	let totalEntries = $state(0);
	let entryDatesSet = $state<Set<string>>(new Set());
	let currentDate = $state(localDate());
	let showAllEntries = $state(false);
	let allEntries = $state<JournalPreview[]>([]);
	let hasMoreEntries = $state(true);
	let loadingMore = $state(false);
	let dateInputEl: HTMLInputElement;

	const PAGE_SIZE = 20;

	const isToday = $derived(currentDate === localDate());
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
		const todayStr = localDate();
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
			const iso = localDate(d);
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
		const today = localDate();
		const iso = localDate(d);
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
		const today = localDate();
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
		if (dateStr === localDate()) return 'Today';
		return new Date(dateStr + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
	}

	async function refreshDates() {
		try {
			const dates = await fetchJournalDates();
			totalEntries = dates.length;
			entryDatesSet = new Set(dates);
		} catch {}
	}

	const autoSave = createAutoSave(async () => {
		await saveJournal(currentDate, content);
		await refreshDates();
	});

	function handleInput() {
		autoSave.trigger();
	}

	onDestroy(() => {
		autoSave.cleanup();
		window.removeEventListener('journal-updated', handleJournalUpdated);
	});

	async function handleJournalUpdated() {
		if (currentDate === localDate()) {
			await loadEntry();
		}
		await refreshDates();
	}

	onMount(async () => {
		await loadEntry();
		await refreshDates();
		window.addEventListener('journal-updated', handleJournalUpdated);
	});
</script>

<div class="jrnl-card">
	<input
		type="date"
		class="jrnl-date-input-hidden"
		bind:this={dateInputEl}
		onchange={handleDatePick}
		max={localDate()}
	/>

	<div class="jrnl-header">
		<button class="jrnl-nav-arrow" onclick={() => navigateDay(-1)} aria-label="Previous day">
			<CaretLeft size={12} weight="bold" />
		</button>
		<button class="jrnl-date-label" onclick={openDatePicker}>
			{formatDateLabel(currentDate)}
			{#if autoSave.saved}
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
			{showAllEntries ? 'Hide' : `${totalEntries} ${totalEntries === 1 ? 'entry' : 'entries'}`}
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

<style>
/* Journal — calm & minimal with dot calendar */
.jrnl-card {
	border-radius: 12px;
	background: var(--card-bg);
	border: 1px solid var(--border);
	padding: 0;
	box-shadow:
		0 1px 2px rgba(0, 0, 0, 0.06),
		0 4px 12px rgba(0, 0, 0, 0.04);
	display: flex;
	flex-direction: column;
	margin-bottom: var(--space-section);
	position: relative;
}

:global([data-theme='dark']) .jrnl-card {
	box-shadow:
		0 1px 2px rgba(0, 0, 0, 0.2),
		0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Hidden native date picker — positioned under the date label so iOS opens it there */
.jrnl-date-input-hidden {
	position: absolute;
	top: 14px;
	left: 50%;
	transform: translateX(-50%);
	opacity: 0;
	width: 1px;
	height: 1px;
	border: none;
	pointer-events: none;
}

/* Header: centered < Today > */
.jrnl-header {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 10px;
	padding: 14px 20px;
}

.jrnl-nav-arrow {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 28px;
	height: 28px;
	border-radius: 6px;
	border: none;
	background: none;
	color: var(--text-tertiary);
	cursor: pointer;
	transition: background 0.15s ease, color 0.15s ease, opacity 0.15s ease;
	-webkit-tap-highlight-color: transparent;
}

/* Hover persists on iOS after tap — acts as the "active" feedback */
.jrnl-nav-arrow:hover {
	background: var(--bg-secondary);
	color: var(--text);
}

.jrnl-nav-arrow:disabled {
	opacity: 0.2;
	cursor: default;
}

.jrnl-nav-arrow:disabled:hover {
	background: none;
	color: var(--text-tertiary);
}

:global([data-theme='dark']) .jrnl-nav-arrow {
	color: var(--text-tertiary);
}

:global([data-theme='dark']) .jrnl-nav-arrow:hover {
	background: var(--bg-hover);
	color: var(--text);
}

/* Date label with inline saved dot */
.jrnl-date-label {
	display: flex;
	align-items: center;
	gap: 6px;
	font-family: var(--font-mono);
	font-size: 10px;
	font-weight: 500;
	text-transform: uppercase;
	letter-spacing: 0.1em;
	color: var(--text-secondary);
	background: none;
	border: none;
	padding: 4px 4px;
	cursor: pointer;
	-webkit-tap-highlight-color: transparent;
	border-bottom: 1px dashed var(--text-tertiary);
}

:global([data-theme='dark']) .jrnl-date-label {
	color: var(--text);
}

.jrnl-saved-dot {
	width: 5px;
	height: 5px;
	border-radius: 50%;
	background: var(--color-green);
	flex-shrink: 0;
}

/* Textarea with ruled lines */
.jrnl-body {
	padding: 0 20px;
}

.jrnl-textarea {
	width: 100%;
	height: 160px;
	border: none;
	color: var(--text);
	font-family: var(--font-sans);
	font-size: 14px;
	line-height: 32px;
	resize: none;
	outline: none;
	padding: 0;
	padding-bottom: 8px;
	overflow-y: auto;
	-webkit-overflow-scrolling: touch;
	scrollbar-width: thin;
	background-color: var(--card-bg);
	background-image:
		repeating-linear-gradient(
			to bottom,
			transparent 0px,
			transparent 25px,
			var(--border) 25px,
			var(--border) 26px,
			transparent 26px,
			transparent 32px
		);
	background-attachment: local;
}

:global([data-theme='dark']) .jrnl-textarea {
	color: #e8e6e1;
	background-color: var(--card-bg);
	background-image:
		repeating-linear-gradient(
			to bottom,
			transparent 0px,
			transparent 25px,
			rgba(255, 255, 255, 0.1) 25px,
			rgba(255, 255, 255, 0.1) 26px,
			transparent 26px,
			transparent 32px
		);
}

.jrnl-textarea::placeholder {
	color: var(--text-tertiary);
	font-style: italic;
}

:global([data-theme='dark']) .jrnl-textarea::placeholder {
	color: #6b6a66;
}

/* Footer: single row — dots, word count, entries */
.jrnl-footer {
	position: relative;
	padding: 10px 20px;
	margin-top: 4px;
	border-top: 1px solid var(--border);
	display: flex;
	align-items: center;
	justify-content: space-between;
}

/* Non-interactive dot indicators */
.jrnl-dots {
	display: flex;
	gap: 6px;
	align-items: center;
	flex-shrink: 0;
}

.jrnl-dot {
	width: 7px;
	height: 7px;
	border-radius: 50%;
	flex-shrink: 0;
}

.jrnl-dot-filled {
	background: var(--accent);
}

.jrnl-dot-empty {
	background: var(--bg-inset);
}

:global([data-theme='dark']) .jrnl-dot-filled {
	background: var(--text);
}

.jrnl-dot-selected {
	width: 9px;
	height: 9px;
	background: transparent;
	border: 2px solid var(--accent);
}

:global([data-theme='dark']) .jrnl-dot-selected {
	border-color: var(--text);
}

.jrnl-wordcount {
	position: absolute;
	left: 50%;
	transform: translateX(-50%);
	font-family: var(--font-mono);
	font-size: 10px;
	color: var(--text-tertiary);
	pointer-events: none;
}

.jrnl-entries-toggle {
	font-family: var(--font-mono);
	font-size: 10px;
	color: var(--text-tertiary);
	background: none;
	border: none;
	border-bottom: 1px dashed var(--text-tertiary);
	cursor: pointer;
	padding: 0 0 1px;
	transition: opacity 0.15s ease;
	-webkit-tap-highlight-color: transparent;
}

.jrnl-entries-toggle:hover {
	opacity: 0.7;
}

/* Animated entry drawer */
.jrnl-entries-drawer {
	max-height: 0;
	overflow: hidden;
	transition: max-height 0.35s ease;
}

.jrnl-entries-drawer-open {
	max-height: 280px;
}

.jrnl-entries-list {
	max-height: 280px;
	overflow-y: auto;
	display: flex;
	flex-direction: column;
	-webkit-overflow-scrolling: touch;
	scrollbar-width: thin;
	border-top: 1px solid var(--border);
}

.jrnl-entry-row {
	display: flex;
	align-items: baseline;
	gap: 12px;
	padding: 10px 20px;
	border: none;
	border-left: 2px solid transparent;
	background: none;
	cursor: pointer;
	text-align: left;
	transition: background 0.15s ease, border-color 0.15s ease;
	-webkit-tap-highlight-color: transparent;
}

.jrnl-entry-row + .jrnl-entry-row {
	border-top: 1px solid var(--border);
}

.jrnl-entry-row:hover {
	background: var(--bg-hover);
}

.jrnl-entry-active {
	background: var(--bg-hover);
	border-left-color: var(--accent);
}

.jrnl-entry-date {
	font-family: var(--font-mono);
	font-size: 11px;
	font-weight: 500;
	color: var(--text-secondary);
	white-space: nowrap;
	flex-shrink: 0;
	min-width: 50px;
}

:global([data-theme='dark']) .jrnl-entry-date {
	color: var(--text);
}

.jrnl-entry-preview {
	font-family: var(--font-sans);
	font-size: 12px;
	color: var(--text-tertiary);
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	line-height: 1.4;
}

:global([data-theme='dark']) .jrnl-entry-preview {
	color: #9b9a96;
}

.jrnl-entries-empty {
	font-family: var(--font-mono);
	font-size: 11px;
	color: var(--text-tertiary);
	text-align: center;
	padding: 16px 0;
}

.jrnl-load-more {
	font-family: var(--font-mono);
	font-size: 10px;
	color: var(--text-tertiary);
	background: none;
	border: none;
	border-top: 1px solid var(--border);
	padding: 10px 20px;
	cursor: pointer;
	text-align: center;
	transition: opacity 0.15s ease;
	-webkit-tap-highlight-color: transparent;
}

.jrnl-load-more:hover {
	opacity: 0.7;
}

.jrnl-load-more:disabled {
	opacity: 0.4;
	cursor: default;
}
</style>
