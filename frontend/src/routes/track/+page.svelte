<script lang="ts">
	import {
		fetchHabitsToday, toggleHabit, toggleWorkout, saveWorkoutNote,
		fetchMoodToday, saveMood, fetchStreaks, fetchHabitsWeek,
		fetchCustomHabits, addCustomHabit, deleteCustomHabit,
		fetchWaterToday, incrementWater, decrementWater,
		fetchAchievements,
		type HabitsToday, type HabitsWeek, type CustomHabit, type Achievement
	} from '$lib/api';
	import MoodSelector from '$lib/components/MoodSelector.svelte';
	import SleepLogger from '$lib/components/SleepLogger.svelte';
	import HabitWeekView from '$lib/components/HabitWeekView.svelte';
	import FocusHeatmap from '$lib/components/FocusHeatmap.svelte';
	import WeeklyReview from '$lib/components/WeeklyReview.svelte';
	import { theme, toggleTheme } from '$lib/theme';
	import { getCached, setCached, clearCached } from '$lib/cache';
	import { onDestroy } from 'svelte';
	import { Check, X, Plus, Minus, Drop, Trophy, Moon, Sun } from 'phosphor-svelte';

	const _c = getCached<any>('track');

	let habits = $state<HabitsToday | null>(_c?.habits ?? null);
	let mood = $state<number | null>(_c?.mood ?? null);
	let streaks = $state<Record<string, number>>(_c?.streaks ?? {});
	let weekData = $state<HabitsWeek | null>(_c?.weekData ?? null);
	let workoutNote = $state('');
	let workoutNoteTimeout: ReturnType<typeof setTimeout> | null = null;
	let customHabits = $state<CustomHabit[]>(_c?.customHabits ?? []);
	let showAddHabit = $state(false);
	let newHabitName = $state('');
	let waterGlasses = $state(_c?.waterGlasses ?? 0);
	let achievements = $state<Achievement[]>([]);

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
		clearCached('home');
	}

	async function handleToggleNightRoutine() {
		if (!habits) return;
		const done = await toggleHabit('night_routine');
		habits = { ...habits, night_routine: done };
		clearCached('home');
	}

	async function handleMoodSelect(n: number) {
		mood = n;
		await saveMood(n);
		habits = await fetchHabitsToday();
		clearCached('home');
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
		clearCached('home');
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

	async function handleWaterIncrement() {
		waterGlasses = await incrementWater();
	}
	async function handleWaterDecrement() {
		waterGlasses = await decrementWater();
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
		if (_c) return;
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
		fetchAchievements().then((data) => { achievements = data.achievements; });
	});

	// Always fetch water data on mount (even if cached) to ensure freshness
	$effect(() => {
		fetchWaterToday().then((g) => { waterGlasses = g; });
	});

	onDestroy(() => {
		if (workoutNoteTimeout) clearTimeout(workoutNoteTimeout);
		setCached('track', { habits, mood, streaks, weekData, customHabits, waterGlasses, achievements });
	});
</script>

<div class="page-header">
	<h1 class="greeting">Track</h1>
	<button class="theme-toggle" onclick={toggleTheme} aria-label="Toggle theme">
		{#if $theme === 'light'}
			<Moon size={18} weight="duotone" />
		{:else}
			<Sun size={18} weight="duotone" />
		{/if}
	</button>
</div>

<p class="habits-date">{formatDate()}</p>

<MoodSelector {mood} onselect={handleMoodSelect} />

<div class="water-widget">
	<div class="water-header">
		<Drop size={16} weight="duotone" />
		<span class="water-label">Water</span>
		<span class="water-count">{waterGlasses} glasses</span>
	</div>
	<div class="water-controls">
		<button class="water-btn" onclick={handleWaterDecrement} disabled={waterGlasses === 0}>
			<Minus size={14} weight="bold" />
		</button>
		<div class="water-dots">
			{#each Array(8) as _, i}
				<span class="water-dot" class:water-dot-filled={i < waterGlasses}></span>
			{/each}
		</div>
		<button class="water-btn" onclick={handleWaterIncrement}>
			<Plus size={14} weight="bold" />
		</button>
	</div>
</div>

{#if habits}
	<div class="habits-list">
		<!-- Focus — auto -->
		<div class="habit-row" class:habit-done={habits.focus_achieved}>
			<div class="habit-check" class:habit-check-done={habits.focus_achieved}>
				{#if habits.focus_achieved}
					<Check size={14} weight="bold" />
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
					<Check size={14} weight="bold" />
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
					<Check size={14} weight="bold" />
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
					<Check size={14} weight="bold" />
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
					<Check size={14} weight="bold" />
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
						<Check size={14} weight="bold" />
					{/if}
				</div>
				<div class="habit-info">
					<span class="habit-name">{ch.name}</span>
				</div>
				{#if streaks[`custom:${ch.name}`]}
					<span class="habit-streak">{streaks[`custom:${ch.name}`]}d</span>
				{/if}
				<button class="custom-habit-delete" onclick={(e) => { e.stopPropagation(); handleDeleteCustomHabit(ch.id, ch.name); }} aria-label="Delete habit">
					<X size={14} weight="bold" />
				</button>
			</div>
		{/each}

		<!-- Add habit row -->
		{#if showAddHabit}
			<div class="habit-row habit-row-last habit-add-row">
				<div class="habit-check habit-add-icon">
					<Plus size={14} weight="bold" />
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
						<X size={14} weight="bold" />
					</button>
				</form>
			</div>
		{:else}
			<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
			<div class="habit-row habit-row-last habit-add-trigger" onclick={() => (showAddHabit = true)}>
				<div class="habit-check habit-add-icon">
					<Plus size={14} weight="bold" />
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

<FocusHeatmap />

<WeeklyReview />

{#if achievements.length > 0}
	<div class="achievements-section">
		<div class="section-header">
			<span class="section-title">Achievements</span>
		</div>
		<div class="achievements-grid">
			{#each achievements as a}
				<div class="achievement-badge">
					<Trophy size={16} weight="duotone" />
					<div class="achievement-info">
						<span class="achievement-name">{a.description}</span>
						<span class="achievement-date">
							{new Date(a.earned_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
						</span>
					</div>
				</div>
			{/each}
		</div>
	</div>
{/if}

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
		border-color: var(--accent);
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
		color: var(--text);
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
		border: 2px dashed var(--border) !important;
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
		border: none;
		background: none;
		padding: 0;
		color: var(--text);
		font-family: var(--font-sans);
		font-size: 15px;
		font-weight: 500;
		outline: none;
	}

	.habit-add-input::placeholder {
		color: var(--text-tertiary);
	}

	.habit-add-submit {
		padding: 6px 12px;
		border: none;
		border-radius: 6px;
		background: var(--accent);
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

	.water-widget {
		border-radius: 10px;
		padding: 14px 16px;
		background: var(--card-bg);
		margin-bottom: 20px;
	}

	.water-header {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 10px;
		color: var(--text-secondary);
	}

	.water-label {
		font-family: var(--font-display);
		font-size: 13px;
		font-weight: 600;
		color: var(--text);
	}

	.water-count {
		font-family: var(--font-mono);
		font-size: 12px;
		color: var(--text-tertiary);
		margin-left: auto;
	}

	.water-controls {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.water-btn {
		width: 30px;
		height: 30px;
		border-radius: 50%;
		border: 1px solid var(--border);
		background: none;
		color: var(--text-secondary);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.15s ease;
		padding: 0;
	}

	.water-btn:hover {
		background: var(--bg-hover);
		color: var(--text);
		border-color: var(--text-tertiary);
	}

	.water-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.water-dots {
		flex: 1;
		display: flex;
		justify-content: center;
		gap: 6px;
	}

	.water-dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--bg-inset);
		border: 1.5px solid var(--border);
		transition: all 0.2s ease;
	}

	.water-dot-filled {
		background: var(--color-blue);
		border-color: var(--color-blue);
	}

	.achievements-section {
		margin-top: 16px;
	}

	.achievements-grid {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.achievement-badge {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 10px 14px;
		border-radius: 8px;
		background: var(--card-bg);
		color: var(--accent);
	}

	.achievement-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.achievement-name {
		font-family: var(--font-display);
		font-size: 13px;
		font-weight: 500;
		color: var(--text);
	}

	.achievement-date {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--text-tertiary);
	}
</style>
