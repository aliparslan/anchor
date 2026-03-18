<script lang="ts">
	import { onMount } from 'svelte';
	import { completePomodoroSession } from '$lib/api';

	async function requestNotificationPermission() {
		if ('Notification' in window && Notification.permission === 'default') {
			const result = await Notification.requestPermission();
			notifPermission = result;
		}
	}

	function notify(title: string, body: string) {
		if ('Notification' in window && Notification.permission === 'granted') {
			new Notification(title, { body, icon: '/icon-192.png' });
		}
	}
	import {
		loadState,
		saveState,
		getRemainingMs,
		isRunning,
		isComplete,
		startTimer,
		pauseTimer,
		resumeTimer,
		completeSegment,
		resetTimer,
		DURATIONS,
		type PomodoroState
	} from '$lib/timer';

	let { totalMinutesToday = $bindable(0) }: { totalMinutesToday: number } = $props();

	let state = $state<PomodoroState>(loadState());
	let remainingMs = $state(0);
	let intervalId: ReturnType<typeof setInterval> | null = null;
	let completing = false;
	let notifPermission = $state<string>('Notification' in globalThis ? Notification.permission : 'denied');

	const FOCUS_GOAL = 240;

	const statusLabel: Record<string, string> = {
		idle: 'Ready',
		working: 'Focus',
		short_break: 'Short Break',
		long_break: 'Long Break'
	};

	function tick() {
		if (isComplete(state)) {
			handleComplete();
			return;
		}
		remainingMs = getRemainingMs(state);
	}

	async function handleComplete() {
		if (completing) return;
		completing = true;
		try {
			if (state.status === 'working') {
				const data = await completePomodoroSession();
				totalMinutesToday = data.total_minutes;
				const done = state.pomodorosCompleted + 1;
				notify('Focus complete', done >= 4 ? 'Long break time.' : 'Take a short break.');
			} else {
				notify('Break over', '');
			}
			state = completeSegment(state);
			remainingMs = 0;
		} finally {
			completing = false;
		}
	}

	function handleStartPause() {
		requestNotificationPermission();
		if (state.status === 'idle') {
			state = startTimer(state);
		} else if (isRunning(state)) {
			state = pauseTimer(state);
		} else if (state.pausedAt !== null) {
			state = resumeTimer(state);
		} else {
			state = startTimer(state);
		}
		remainingMs = getRemainingMs(state);
	}

	function handleReset() {
		state = resetTimer();
		remainingMs = 0;
	}

	function formatTime(ms: number): string {
		const totalSec = Math.ceil(ms / 1000);
		const m = Math.floor(totalSec / 60);
		const s = totalSec % 60;
		return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
	}

	function displayTime(): string {
		if (state.status === 'idle') return '25:00';
		return formatTime(remainingMs);
	}

	$effect(() => {
		if (intervalId) clearInterval(intervalId);
		if (isRunning(state)) {
			intervalId = setInterval(tick, 250);
		}
		return () => {
			if (intervalId) clearInterval(intervalId);
		};
	});

	onMount(() => {
		state = loadState();
		remainingMs = getRemainingMs(state);
		if (isComplete(state)) {
			handleComplete();
		}
	});

	const progressPercent = $derived(Math.min(100, (totalMinutesToday / FOCUS_GOAL) * 100));
	const focusHours = $derived(Math.floor(totalMinutesToday / 60));
	const focusMins = $derived(totalMinutesToday % 60);
</script>

<div class="pomodoro-widget">
	<div class="pomodoro-header">
		<span class="pomodoro-status">{statusLabel[state.status]}</span>
		<div class="pomodoro-dots">
			{#each Array(4) as _, i}
				<span class="pomodoro-dot" class:filled={i < state.pomodorosCompleted}></span>
			{/each}
		</div>
	</div>

	<div class="pomodoro-time">{displayTime()}</div>

	<div class="pomodoro-controls">
		<button class="pomodoro-btn" onclick={handleStartPause} aria-label={isRunning(state) ? 'Pause' : 'Start'}>
			{#if isRunning(state)}
				<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none">
					<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>
				</svg>
			{:else}
				<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none">
					<polygon points="6,4 20,12 6,20"/>
				</svg>
			{/if}
		</button>
		<button class="pomodoro-btn" onclick={handleReset} aria-label="Reset">
			<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
				<polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
			</svg>
		</button>
	</div>

	<div class="pomodoro-progress-section">
		<div class="pomodoro-progress-bar">
			<div class="pomodoro-progress-fill" style="width: {progressPercent}%"></div>
		</div>
		<span class="pomodoro-progress-label">
			{focusHours}h{focusMins > 0 ? ` ${focusMins}m` : ''} / 4h
		</span>
	</div>
	{#if notifPermission === 'default'}
		<button class="pomodoro-notif-btn" onclick={requestNotificationPermission}>
			Enable notifications
		</button>
	{/if}
</div>
