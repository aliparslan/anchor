<script lang="ts">
	import {
		fetchHabitsToday, toggleHabit, toggleWorkout, saveWorkoutNote,
		fetchMoodToday, saveMood, fetchStreaks, fetchHabitsWeek,
		fetchCustomHabits, addCustomHabit, deleteCustomHabit,
		type HabitsToday, type HabitsWeek, type CustomHabit
	} from '$lib/api';
	import MoodSelector from '$lib/components/MoodSelector.svelte';
	import SleepLogger from '$lib/components/SleepLogger.svelte';
	import HabitWeekView from '$lib/components/HabitWeekView.svelte';
	import WeeklyReview from '$lib/components/WeeklyReview.svelte';
	import { theme, toggleTheme } from '$lib/theme';

	let habits = $state<HabitsToday | null>(null);
	let mood = $state<number | null>(null);
	let streaks = $state<Record<string, number>>({});
	let weekData = $state<HabitsWeek | null>(null);
	let workoutNote = $state('');
	let workoutNoteTimeout: ReturnType<typeof setTimeout> | null = null;
	let customHabits = $state<CustomHabit[]>([]);
	let showAddHabit = $state(false);
	let newHabitName = $state('');

	function formatDate(): string {
		return new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
	}

	function focusLabel(minutes: number): string {
		const h = Math.floor(minutes / 60);
		const m = minutes % 60;
		if (h === 0) return `${m}m / 4h`;
		if (m === 0) return `${h}h / 4h`;
		return `${h}h ${m}m / 4h`;
	}

	async function handleToggleWorkout() {
		if (!habits) return;
		const done = await toggleWorkout();
		habits = { ...habits, workout: done ? 1 : 0 };
		if (!done) workoutNote = '';
	}

	async function handleToggleNightRoutine() {
		if (!habits) return;
		const done = await toggleHabit('night_routine');
		habits = { ...habits, night_routine: done };
	}

	async function handleMoodSelect(n: number) {
		mood = n;
		await saveMood(n);
		// Refresh habits to update mood_logged
		habits = await fetchHabitsToday();
	}

	function handleWorkoutNoteInput() {
		if (workoutNoteTimeout) clearTimeout(workoutNoteTimeout);
		workoutNoteTimeout = setTimeout(() => {
			saveWorkoutNote(workoutNote);
		}, 1500);
	}

	async function handleToggleCustomHabit(name: string) {
		if (!habits) return;
		const done = await toggleHabit(name);
		habits = {
			...habits,
			custom_habits: { ...habits.custom_habits, [name]: done }
		};
	}

	async function handleAddCustomHabit() {
		const trimmed = newHabitName.trim();
		if (!trimmed) return;
		const habit = await addCustomHabit(trimmed);
		customHabits = [...customHabits, habit];
		if (habits) {
			habits = {
				...habits,
				custom_habits: { ...habits.custom_habits, [trimmed]: false }
			};
		}
		newHabitName = '';
		showAddHabit = false;
		weekData = await fetchHabitsWeek();
	}

	async function handleDeleteCustomHabit(id: number, name: string) {
		await deleteCustomHabit(id);
		customHabits = customHabits.filter((h) => h.id !== id);
		if (habits) {
			const { [name]: _, ...rest } = habits.custom_habits;
			habits = { ...habits, custom_habits: rest };
		}
		weekData = await fetchHabitsWeek();
	}

	$effect(() => {
		Promise.all([
			fetchHabitsToday(),
			fetchMoodToday(),
			fetchStreaks(),
			fetchHabitsWeek(),
			fetchCustomHabits()
		]).then(([h, m, s, w, ch]) => {
			habits = h;
			mood = m?.mood ?? null;
			streaks = s;
			weekData = w;
			customHabits = ch;
		});
	});
</script>

<div class="page-header">
	<h1 class="greeting">Track</h1>
	<button class="theme-toggle" onclick={toggleTheme} aria-label="Toggle theme">
		{#if $theme === 'light'}
			<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
		{:else}
			<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
		{/if}
	</button>
</div>

<p class="habits-date">{formatDate()}</p>

<MoodSelector {mood} onselect={handleMoodSelect} />

{#if habits}
	<div class="habits-list">
		<!-- Focus — auto -->
		<div class="habit-row" class:habit-done={habits.focus_achieved}>
			<div class="habit-check" class:habit-check-done={habits.focus_achieved}>
				{#if habits.focus_achieved}
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
				{/if}
			</div>
			<div class="habit-info">
				<span class="habit-name">Focus</span>
				<span class="habit-sub">{focusLabel(habits.focus_minutes)}</span>
			</div>
			{#if streaks.focus}
				<span class="habit-streak">{streaks.focus}d</span>
			{/if}
			<span class="habit-auto-badge">auto</span>
		</div>

		<!-- Workout — manual toggle -->
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div class="habit-row" class:habit-done={habits.workout === 1} onclick={handleToggleWorkout}>
			<div class="habit-check" class:habit-check-done={habits.workout === 1}>
				{#if habits.workout === 1}
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
				{/if}
			</div>
			<div class="habit-info">
				<span class="habit-name">Workout</span>
			</div>
			{#if streaks.workout}
				<span class="habit-streak">{streaks.workout}d</span>
			{/if}
		</div>

		{#if habits.workout === 1}
			<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
			<div class="workout-note-row" onclick={(e) => e.stopPropagation()}>
				<input
					type="text"
					class="workout-note-input"
					placeholder="What did you do?"
					bind:value={workoutNote}
					oninput={handleWorkoutNoteInput}
				/>
			</div>
		{/if}

		<!-- Night Routine — manual toggle -->
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div class="habit-row" class:habit-done={habits.night_routine} onclick={handleToggleNightRoutine}>
			<div class="habit-check" class:habit-check-done={habits.night_routine}>
				{#if habits.night_routine}
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
				{/if}
			</div>
			<div class="habit-info">
				<span class="habit-name">Night Routine</span>
			</div>
			{#if streaks.night_routine}
				<span class="habit-streak">{streaks.night_routine}d</span>
			{/if}
		</div>

		<!-- Sleep tracked — auto -->
		<div class="habit-row" class:habit-done={habits.sleep_tracked}>
			<div class="habit-check" class:habit-check-done={habits.sleep_tracked}>
				{#if habits.sleep_tracked}
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
				{/if}
			</div>
			<div class="habit-info">
				<span class="habit-name">Sleep tracked</span>
			</div>
			{#if streaks.sleep}
				<span class="habit-streak">{streaks.sleep}d</span>
			{/if}
			<span class="habit-auto-badge">auto</span>
		</div>

		<!-- Mood logged — auto -->
		<div class="habit-row" class:habit-done={habits.mood_logged} class:habit-row-last={customHabits.length === 0 && !showAddHabit}>
			<div class="habit-check" class:habit-check-done={habits.mood_logged}>
				{#if habits.mood_logged}
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
				{/if}
			</div>
			<div class="habit-info">
				<span class="habit-name">Mood logged</span>
			</div>
			{#if streaks.mood}
				<span class="habit-streak">{streaks.mood}d</span>
			{/if}
			<span class="habit-auto-badge">auto</span>
		</div>

		<!-- Custom habits -->
		{#each customHabits as ch, ci}
			<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
			<div class="habit-row" class:habit-done={habits.custom_habits?.[ch.name]} class:habit-row-last={ci === customHabits.length - 1 && !showAddHabit} onclick={() => handleToggleCustomHabit(ch.name)}>
				<div class="habit-check" class:habit-check-done={habits.custom_habits?.[ch.name]}>
					{#if habits.custom_habits?.[ch.name]}
						<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
					{/if}
				</div>
				<div class="habit-info">
					<span class="habit-name">{ch.name}</span>
				</div>
				{#if streaks[`custom:${ch.name}`]}
					<span class="habit-streak">{streaks[`custom:${ch.name}`]}d</span>
				{/if}
				<button class="custom-habit-delete" onclick={(e) => { e.stopPropagation(); handleDeleteCustomHabit(ch.id, ch.name); }} aria-label="Delete habit">
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
				</button>
			</div>
		{/each}

		<!-- Add habit row -->
		{#if showAddHabit}
			<div class="habit-row habit-row-last habit-add-row">
				<div class="habit-check habit-add-icon">
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
				</div>
				<form class="habit-add-form" onsubmit={(e) => { e.preventDefault(); handleAddCustomHabit(); }}>
					<input
						type="text"
						class="habit-add-input"
						placeholder="Habit name..."
						bind:value={newHabitName}
						autofocus
					/>
					<button type="submit" class="habit-add-submit" disabled={!newHabitName.trim()}>Add</button>
					<button type="button" class="habit-add-cancel" onclick={() => { showAddHabit = false; newHabitName = ''; }}>
						<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
					</button>
				</form>
			</div>
		{:else}
			<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
			<div class="habit-row habit-row-last habit-add-trigger" onclick={() => (showAddHabit = true)}>
				<div class="habit-check habit-add-icon">
					<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
				</div>
				<div class="habit-info">
					<span class="habit-name habit-add-label">Add habit</span>
				</div>
			</div>
		{/if}
	</div>
{/if}

<div class="track-spacer"></div>

<SleepLogger />

<HabitWeekView data={weekData} />

<WeeklyReview />

<style>
	.habit-streak {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--text-tertiary);
		margin-right: 4px;
	}

	.workout-note-row {
		padding: 0 16px 12px;
		border-bottom: 1px solid var(--border);
		background: var(--bg-secondary);
	}

	.workout-note-input {
		width: 100%;
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 8px 10px;
		background: var(--bg);
		color: var(--text);
		font-family: var(--font-sans);
		font-size: 13px;
		outline: none;
		transition: border-color 0.15s ease;
	}

	.workout-note-input:focus {
		border-color: var(--text-tertiary);
	}

	.track-spacer {
		height: 20px;
	}

	.custom-habit-delete {
		flex-shrink: 0;
		width: 24px;
		height: 24px;
		border-radius: 6px;
		border: none;
		background: none;
		color: var(--text-tertiary);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		opacity: 0;
		transition: all 0.15s ease;
		padding: 0;
	}

	.habit-row:hover .custom-habit-delete {
		opacity: 1;
	}

	.custom-habit-delete:hover {
		background: var(--bg-hover);
		color: var(--color-yt);
	}

	.habit-add-trigger {
		cursor: pointer;
		opacity: 0.5;
		transition: opacity 0.15s ease;
	}

	.habit-add-trigger:hover {
		opacity: 0.8;
	}

	.habit-add-icon {
		border-style: dashed !important;
		border-color: var(--text-tertiary) !important;
		background: none !important;
		color: var(--text-tertiary);
	}

	.habit-add-label {
		color: var(--text-tertiary) !important;
	}

	.habit-add-row {
		padding: 10px 16px;
	}

	.habit-add-form {
		flex: 1;
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.habit-add-input {
		flex: 1;
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 6px 10px;
		background: var(--bg);
		color: var(--text);
		font-family: var(--font-sans);
		font-size: 13px;
		outline: none;
		transition: border-color 0.15s ease;
	}

	.habit-add-input:focus {
		border-color: var(--text-tertiary);
	}

	.habit-add-submit {
		padding: 6px 12px;
		border: none;
		border-radius: 6px;
		background: var(--color-habits);
		color: white;
		font-family: var(--font-display);
		font-size: 12px;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.15s ease;
	}

	.habit-add-submit:disabled {
		opacity: 0.4;
		cursor: default;
	}

	.habit-add-cancel {
		width: 24px;
		height: 24px;
		border-radius: 6px;
		border: none;
		background: none;
		color: var(--text-tertiary);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0;
		transition: all 0.15s ease;
	}

	.habit-add-cancel:hover {
		background: var(--bg-hover);
		color: var(--text);
	}

	@media (max-width: 600px) {
		.custom-habit-delete {
			opacity: 1;
		}
	}
</style>
