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

	let { totalMinutesToday = $bindable(0), workDuration = 25, focusGoal = 240 }: { totalMinutesToday: number; workDuration?: number; focusGoal?: number } = $props();

	let state = $state<PomodoroState>(loadState());
	let remainingMs = $state(0);

	// Override working duration from settings
	$effect(() => {
		DURATIONS.working = 5 * 1000; // TODO: revert to workDuration * 60 * 1000
	});
	let intervalId: ReturnType<typeof setInterval> | null = null;
	let completing = false;
	let notifPermission = $state<string>('Notification' in globalThis ? Notification.permission : 'denied');

	const goalHours = $derived(Math.floor(focusGoal / 60));
	const goalMins = $derived(focusGoal % 60);

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
		if (state.status === 'idle') return formatTime(workDuration * 60 * 1000);
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
		<div class="pomo-time" aria-label="Timer: {displayTime()}" role="timer">{displayTime()}</div>
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
		{focusHours}h{focusMins > 0 ? ` ${focusMins}m` : ''} / {goalHours}h{goalMins > 0 ? `${goalMins}m` : ''}
	</span>
</div>

<style>
	.pomo-device {
		border-radius: var(--radius-lg);
		background: var(--card-bg);
		border: 1px solid var(--border);
		padding: var(--space-lg);
		box-shadow: var(--shadow-card);
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
		margin-bottom: var(--space-widget);
	}

	.pomo-screen {
		background: var(--bg-inset);
		border-radius: var(--radius-md);
		padding: 20px 16px 16px;
		border: 1px solid color-mix(in srgb, var(--text) 6%, transparent);
		box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.1);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
	}

	:global([data-theme='dark']) .pomo-screen {
		box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);
	}

	.pomo-session {
		font-family: var(--font-mono);
		font-size: 10px;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: var(--text-secondary);
	}

	.pomo-time {
		font-family: var(--font-mono);
		font-size: 52px;
		font-weight: 400;
		font-variant-numeric: tabular-nums;
		letter-spacing: -0.03em;
		line-height: 1;
		color: var(--text);
		padding: 8px 0;
	}

	.pomo-screen-status {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		margin-top: 4px;
	}

	.pomo-status-label {
		font-family: var(--font-mono);
		font-size: 11px;
		font-weight: 500;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.pomo-dots {
		display: flex;
		gap: 6px;
	}

	.pomo-dot {
		width: 8px;
		height: 8px;
		border-radius: var(--radius-full);
		background: color-mix(in srgb, var(--text) 10%, transparent);
		transition: all 0.2s ease;
	}

	.pomo-dot-filled {
		background: var(--accent);
		box-shadow: none;
		animation: dotPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
	}

	@keyframes dotPop {
		0% { transform: scale(0.5); }
		50% { transform: scale(1.3); }
		100% { transform: scale(1); }
	}

	.pomo-controls {
		display: flex;
		gap: 8px;
	}

	.pomo-btn {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 10px 14px;
		border-radius: var(--radius-md);
		border: 1px solid var(--border);
		cursor: pointer;
		transition: all 0.1s ease;
		box-shadow: 0 2px 0 color-mix(in srgb, black 10%, transparent);
	}

	.pomo-btn:active {
		box-shadow: none;
		transform: translateY(2px);
	}

	.pomo-btn-label {
		font-family: var(--font-sans);
		font-size: 11px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
	}

	.pomo-btn-icon {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.pomo-btn-primary {
		background: var(--accent);
		color: var(--bg);
		border-color: var(--accent);
		box-shadow: 0 2px 0 color-mix(in srgb, black 20%, transparent);
	}

	.pomo-btn-primary:hover {
		background: var(--accent-hover);
	}

	.pomo-btn-active {
		background: var(--text-secondary);
		border-color: var(--text-secondary);
		box-shadow: 0 2px 0 color-mix(in srgb, black 15%, transparent);
	}

	.pomo-btn-secondary {
		background: var(--card-bg);
		color: var(--text-secondary);
	}

	:global([data-theme='dark']) .pomo-btn-secondary {
		background: var(--bg-inset);
		color: var(--text-tertiary);
	}

	.pomo-btn-secondary:hover {
		background: var(--bg-hover);
		color: var(--text);
	}

	:global([data-theme='dark']) .pomo-btn-secondary:hover {
		background: var(--border);
		color: var(--text);
	}

	.pomo-grille {
		display: grid;
		grid-template-columns: repeat(24, 1fr);
		gap: 3px;
		padding: 0 6px;
		justify-items: center;
	}

	.pomo-grille-dot {
		width: 5px;
		height: 5px;
		border-radius: var(--radius-full);
		background: color-mix(in srgb, var(--text) 8%, transparent);
		transition: background 0.2s ease;
	}

	.pomo-grille-dot-filled {
		background: var(--accent);
	}

	.pomo-focus-label {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--text-tertiary);
		text-align: center;
	}
</style>
