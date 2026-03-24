<script lang="ts">
	import {
		fetchHabitsToday, toggleHabit, toggleWorkout, saveWorkoutNote,
		fetchMoodToday, saveMood, fetchStreaks, fetchHabitsWeek,
		fetchCustomHabits, addCustomHabit, deleteCustomHabit,
		fetchWaterToday, incrementWater, decrementWater, setWater, fetchWaterWeek,
		type HabitsToday, type HabitsWeek, type CustomHabit, type WaterDay
	} from '$lib/api';
	import MoodSelector from '$lib/components/MoodSelector.svelte';
	import SleepLogger from '$lib/components/SleepLogger.svelte';
	import HabitWeekView from '$lib/components/HabitWeekView.svelte';
	import FocusHeatmap from '$lib/components/FocusHeatmap.svelte';
	import WeeklyReview from '$lib/components/WeeklyReview.svelte';
	import { focusLabel } from '$lib/utils';
	import { getCached, setCached, clearCached } from '$lib/cache';
	import { onDestroy } from 'svelte';
	import { tweened } from 'svelte/motion';
	import { cubicOut } from 'svelte/easing';
	import { Check, X, Plus, PintGlass, CheckCircle } from 'phosphor-svelte';
	import { tap, success } from '$lib/haptics';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SectionHeader from '$lib/components/SectionHeader.svelte';

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
	const displayedMl = tweened((_c?.waterGlasses ?? 0) * 250, { easing: cubicOut });

	$effect(() => {
		const targetMl = waterGlasses * 250;
		displayedMl.set(targetMl, { duration: Math.min(800, Math.abs(targetMl - $displayedMl) / 250 * 200) });
	});

	function formatDate(): string {
		return new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
	}

	function focusLabelWithGoal(minutes: number): string {
		return `${focusLabel(minutes)} / 4h`;
	}

	async function handleToggleWorkout() {
		if (!habits) return;
		tap();
		const done = await toggleWorkout();
		habits = { ...habits, workout: done ? 1 : 0 };
		if (!done) workoutNote = '';
		clearCached('home');
	}

	async function handleToggleNightRoutine() {
		if (!habits) return;
		tap();
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
		tap();
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

	let waterWeek = $state<WaterDay[]>([]);
	let waterExpanded = $state(false);
	let waterCelebrated = $state(false);
	let cupsContainer: HTMLDivElement;
	let displayedGlasses = $state(_c?.waterGlasses ?? 0);
	let glassStepTimer: ReturnType<typeof setTimeout> | null = null;

	function animateGlasses(target: number) {
		if (glassStepTimer) clearTimeout(glassStepTimer);
		function step() {
			if (displayedGlasses === target) return;
			displayedGlasses += displayedGlasses < target ? 1 : -1;
			if (displayedGlasses !== target) {
				glassStepTimer = setTimeout(step, 100);
			}
		}
		step();
	}

	$effect(() => {
		if (displayedGlasses >= 8 && !waterCelebrated) {
			waterCelebrated = true;
			if (cupsContainer) {
				const cups = cupsContainer.querySelectorAll('.water-cup');
				cups.forEach((cup, i) => {
					cup.animate([
						{ transform: 'scale(1)' },
						{ transform: 'scale(1.25) rotate(-8deg)' },
						{ transform: 'scale(1.1) rotate(4deg)' },
						{ transform: 'scale(1) rotate(0)' }
					], { duration: 400, easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)', delay: i * 50 });
				});
			}
		} else if (displayedGlasses < 8 && waterCelebrated) {
			waterCelebrated = false;
		}
	});

	async function handleWaterIncrement() {
		tap();
		waterGlasses = await incrementWater();
		animateGlasses(waterGlasses);
	}
	async function handleWaterDecrement() {
		tap();
		waterGlasses = await decrementWater();
		animateGlasses(waterGlasses);
	}
	async function handleWaterTap(target: number) {
		tap();
		waterGlasses = target;
		animateGlasses(target);
		setWater(target).then((actual) => {
			if (actual !== target) { waterGlasses = actual; animateGlasses(actual); }
		});
	}
	async function toggleWaterInsights() {
		waterExpanded = !waterExpanded;
		if (waterExpanded && waterWeek.length === 0) {
			waterWeek = await fetchWaterWeek();
		}
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
	});

	// Always fetch water data on mount (even if cached) to ensure freshness
	$effect(() => {
		fetchWaterToday().then((g) => {
			if (g !== waterGlasses) { waterGlasses = g; animateGlasses(g); }
		});
	});

	onDestroy(() => {
		if (workoutNoteTimeout) clearTimeout(workoutNoteTimeout);
		if (glassStepTimer) clearTimeout(glassStepTimer);
		setCached('track', { habits, mood, streaks, weekData, customHabits, waterGlasses });
	});
</script>

<PageHeader title="Track" />

<p class="habits-date">{formatDate()}</p>

<SectionHeader title="Mood" />
<MoodSelector {mood} onselect={handleMoodSelect} />

<SectionHeader title="Hydration" style="margin-top: var(--space-widget)" />
<div class="water-widget">
	<div class="water-header">
		<span class="water-ml" class:water-ml-complete={waterGlasses >= 8}>{Math.round($displayedMl).toLocaleString()}</span><span class="water-ml-total">/2,000</span><span class="water-ml-unit">ml</span>
	</div>
	<div class="water-cups" bind:this={cupsContainer}>
		{#each Array(8) as _, i}
			<button class="water-cup" class:water-cup-filled={i < displayedGlasses} onclick={() => handleWaterTap(i < waterGlasses && i === waterGlasses - 1 ? i : i + 1)} aria-label="Glass {i + 1}">
				<PintGlass size={28} weight={i < displayedGlasses ? "fill" : "duotone"} />
			</button>
		{/each}
	</div>
	<button class="water-insights-toggle" onclick={toggleWaterInsights}>
		{waterExpanded ? 'Hide' : 'View Hydration'}
	</button>
	{#if waterExpanded}
		<div class="water-chart">
			{#each waterWeek as day}
				<div class="water-chart-col">
					{#if day.glasses >= 8}
						<div class="water-chart-check">
							<CheckCircle size={14} weight="fill" />
						</div>
					{/if}
					<div class="water-chart-bar-wrap">
						<div class="water-chart-bar-bg"></div>
						<div class="water-chart-bar" style="height: {Math.min(100, (day.glasses / 8) * 100)}%"></div>
					</div>
					<span class="water-chart-label">{new Date(day.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short' }).slice(0, 3)}</span>
				</div>
			{/each}
			{#if waterWeek.length === 0}
				<span class="water-chart-empty">No data yet</span>
			{/if}
		</div>
	{/if}
</div>

<SectionHeader title="Habits" style="margin-top: var(--space-widget)" />
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
				<span class="habit-sub">{focusLabelWithGoal(habits.focus_minutes)}</span>
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
				<div class="habit-add-circle"></div>
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
				<div class="habit-add-circle"></div>
				<div class="habit-info">
					<span class="habit-name habit-add-label">Add habit</span>
				</div>
			</div>
		{/if}
	</div>
{/if}

<div class="track-spacer"></div>

<SectionHeader title="Sleep" />
<SleepLogger />

<SectionHeader title="Insights" style="margin-top: var(--space-widget)" />

<HabitWeekView data={weekData} />

<FocusHeatmap />

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
		border-radius: var(--radius-sm);
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
		height: var(--space-widget);
	}

	.custom-habit-delete {
		flex-shrink: 0;
		width: 24px;
		height: 24px;
		border-radius: var(--radius-sm);
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

	.habit-add-circle {
		width: 20px;
		height: 20px;
		min-width: 20px;
		border-radius: var(--radius-full);
		border: 2px dashed var(--border);
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
		border-radius: var(--radius-sm);
		background: var(--accent);
		color: var(--bg);
		font-family: var(--font-sans);
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
		border-radius: var(--radius-sm);
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
		border-radius: var(--radius-md);
		padding: var(--space-lg);
		background: var(--card-bg);
		border: 1px solid var(--border);
		margin-bottom: var(--space-widget);
	}

	.water-header {
		display: flex;
		align-items: baseline;
		gap: 0;
		margin-bottom: 12px;
	}

	.water-ml {
		font-family: var(--font-mono);
		font-size: 28px;
		font-weight: 500;
		color: var(--text);
		letter-spacing: -0.02em;
		transition: color 0.3s ease;
	}

	.water-ml-complete {
		color: var(--color-blue);
	}

	.water-ml-total {
		font-family: var(--font-mono);
		font-size: 16px;
		font-weight: 400;
		color: var(--text-tertiary);
	}

	.water-ml-unit {
		font-family: var(--font-mono);
		font-size: 12px;
		font-weight: 400;
		color: var(--text-tertiary);
		margin-left: 2px;
	}

	.water-cups {
		display: flex;
		justify-content: space-between;
		gap: 2px;
		margin-bottom: 12px;
	}

	.water-cup {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 6px 0;
		border: none;
		background: none;
		color: var(--border);
		cursor: pointer;
		transition: color var(--ease-micro), background var(--ease-micro);
		border-radius: var(--radius-sm);
	}

	.water-cup:hover {
		background: var(--bg-hover);
	}

	.water-cup:active {
		transform: scale(0.9);
	}

	.water-cup-filled {
		color: var(--color-blue);
	}

	.water-insights-toggle {
		display: block;
		width: 100%;
		padding: 10px;
		border: none;
		border-top: 1px solid var(--border);
		background: none;
		color: var(--color-blue);
		font-family: var(--font-sans);
		font-size: 13px;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.15s ease;
	}

	.water-insights-toggle:hover {
		opacity: 0.7;
	}

	.water-chart {
		display: flex;
		justify-content: space-around;
		align-items: flex-end;
		gap: 6px;
		padding: 16px 0 4px;
		height: 140px;
	}

	.water-chart-col {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
		height: 100%;
	}

	.water-chart-check {
		color: var(--color-blue);
		flex-shrink: 0;
	}

	.water-chart-bar-wrap {
		flex: 1;
		width: 100%;
		display: flex;
		align-items: flex-end;
		justify-content: center;
		position: relative;
	}

	.water-chart-bar-bg {
		position: absolute;
		bottom: 0;
		width: 70%;
		max-width: 24px;
		height: 100%;
		background: color-mix(in srgb, var(--color-blue) 12%, transparent);
		border-radius: var(--radius-sm);
	}

	.water-chart-bar {
		width: 70%;
		max-width: 24px;
		background: var(--color-blue);
		border-radius: var(--radius-sm);
		min-height: 4px;
		transition: height 0.3s ease;
		position: relative;
		z-index: 1;
	}

	.water-chart-label {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--text-tertiary);
		flex-shrink: 0;
	}

	.water-chart-empty {
		font-size: 13px;
		color: var(--text-tertiary);
		text-align: center;
		width: 100%;
		padding: 24px 0;
	}

	/* Habits page */
	.habits-date {
		font-family: var(--font-display);
		font-size: 13px;
		color: var(--text-tertiary);
		margin-bottom: var(--space-widget);
		margin-top: -14px;
	}

	.habits-list {
		border-radius: var(--radius-md);
		background: var(--card-bg);
		border: 1px solid var(--border);
		overflow: hidden;
		padding: 4px 0;
	}

	.habit-row {
		display: flex;
		align-items: center;
		gap: 14px;
		padding: 14px 16px;
		border-bottom: 1px solid var(--border);
		cursor: pointer;
		transition: background 0.15s ease, transform 0.15s ease;
		user-select: none;
	}

	.habit-row.habit-row-last {
		border-bottom: none;
	}

	.habit-row:hover {
		background: var(--bg-hover);
	}

	.habit-row:active {
		transform: scale(0.98);
	}

	.habit-check {
		width: 22px;
		height: 22px;
		border-radius: var(--radius-full);
		border: 2px solid var(--border);
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		color: var(--bg);
		transition: all 0.15s ease;
	}

	.habit-check.habit-check-done {
		background: var(--accent);
		border-color: var(--accent);
		animation: checkPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
	}

	@keyframes checkPop {
		0% { transform: scale(0.8); }
		50% { transform: scale(1.15); }
		100% { transform: scale(1); }
	}

	.habit-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.habit-name {
		font-family: var(--font-display);
		font-size: 15px;
		font-weight: 500;
		color: var(--text);
	}

	.habit-done .habit-name {
		color: var(--text-secondary);
	}

	.habit-sub {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--text-tertiary);
	}

	.habit-auto-badge {
		font-size: 11px;
		color: var(--text-tertiary);
		font-family: var(--font-mono);
	}

</style>
