<script lang="ts">
	import { onMount } from 'svelte';
	import { completePomodoroSession } from '$lib/api';
	import { formatTime } from '$lib/format';
	import { Play, Pause, ArrowCounterClockwise } from 'phosphor-svelte';
	import { tap, success } from '$lib/haptics';

	async function requestNotificationPermission() {
		if ('Notification' in window && Notification.permission === 'default') {
			const result = await Notification.requestPermission();
			notifPermission = result;
		}
	}

	async function notify(title: string, body: string) {
		if (!('serviceWorker' in navigator)) return;
		try {
			const reg = await navigator.serviceWorker.ready;
			await reg.showNotification(title, {
				body,
				icon: '/icon-192.png',
				badge: '/icon-192.png',
				tag: 'anchor-timer',
				vibrate: [200, 100, 200]
			});
		} catch {}
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
		scheduleNotification,
		markNotified,
		wasNotified,
		getSessionId,
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
		scheduleNotification({ ...state, startedAt: null });
		const sid = getSessionId(state);
		try {
			if (state.status === 'working') {
				const data = await completePomodoroSession();
				totalMinutesToday = data.total_minutes;
				if (!wasNotified(sid)) {
					const done = state.pomodorosCompleted + 1;
					notify('Focus complete', done >= 4 ? 'Long break time.' : 'Take a short break.');
					markNotified(sid);
				}
			} else if (!wasNotified(sid)) {
				notify('Break over', '');
				markNotified(sid);
			}
			state = completeSegment(state);
			remainingMs = 0;
		} finally {
			completing = false;
		}
	}

	function handleStartPause() {
		tap();
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
		scheduleNotification(state);
	}

	function handleReset() {
		state = resetTimer();
		remainingMs = 0;
		scheduleNotification(state);
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
		} else if (isRunning(state)) {
			scheduleNotification(state);
		}
	});

	const filledDots = $derived(Math.min(96, Math.floor(totalMinutesToday / 2.5)));
	const focusHours = $derived(Math.floor(totalMinutesToday / 60));
	const focusMins = $derived(totalMinutesToday % 60);
</script>

<div class="pomo-device">
	<div class="pomo-screen">
		<span class="pomo-session">Session {state.pomodorosCompleted + 1}</span>
		<div class="pomo-time">{displayTime()}</div>
		<div class="pomo-screen-status">
			<span class="pomo-status-label">{statusLabel[state.status]}</span>
			<div class="pomo-dots">
				{#each Array(4) as _, i}
					<span class="pomo-dot" class:pomo-dot-filled={i < state.pomodorosCompleted}></span>
				{/each}
			</div>
		</div>
	</div>

	<div class="pomo-controls">
		<button class="pomo-btn pomo-btn-primary" class:pomo-btn-active={isRunning(state)} onclick={handleStartPause}>
			<span class="pomo-btn-label">{isRunning(state) ? 'Pause' : state.pausedAt !== null ? 'Resume' : 'Start'}</span>
			<span class="pomo-btn-icon">
				{#if isRunning(state)}
					<Pause size={16} weight="fill" />
				{:else}
					<Play size={16} weight="fill" />
				{/if}
			</span>
		</button>
		<button class="pomo-btn pomo-btn-secondary" onclick={handleReset}>
			<span class="pomo-btn-label">Reset</span>
			<span class="pomo-btn-icon">
				<ArrowCounterClockwise size={14} weight="bold" />
			</span>
		</button>
	</div>

	<div class="pomo-grille">
		{#each Array(96) as _, i}
			{@const col = i % 24}
			{@const row = Math.floor(i / 24)}
			{@const dotIndex = col * 4 + (3 - row)}
			<span class="pomo-grille-dot" class:pomo-grille-dot-filled={dotIndex < filledDots}></span>
		{/each}
	</div>
	<span class="pomo-focus-label">
		{focusHours}h{focusMins > 0 ? ` ${focusMins}m` : ''} / 4h
	</span>
</div>
