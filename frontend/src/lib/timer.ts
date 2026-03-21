export type TimerStatus = 'idle' | 'working' | 'short_break' | 'long_break';

export interface PomodoroState {
	status: TimerStatus;
	startedAt: number | null;
	pausedAt: number | null;
	elapsed: number;
	pomodorosCompleted: number;
}

const STORAGE_KEY = 'anchor:pomodoro_state';

const DEFAULT_STATE: PomodoroState = {
	status: 'idle',
	startedAt: null,
	pausedAt: null,
	elapsed: 0,
	pomodorosCompleted: 0
};

export const DURATIONS: Record<TimerStatus, number> = {
	idle: 0,
	working: 25 * 60 * 1000,
	short_break: 5 * 60 * 1000,
	long_break: 15 * 60 * 1000
};

export function loadState(): PomodoroState {
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (raw) return JSON.parse(raw);
	} catch {}
	return { ...DEFAULT_STATE };
}

export function saveState(state: PomodoroState): void {
	localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function getElapsedMs(state: PomodoroState): number {
	if (state.startedAt === null) return state.elapsed;
	if (state.pausedAt !== null) return state.elapsed;
	return state.elapsed + (Date.now() - state.startedAt);
}

export function getRemainingMs(state: PomodoroState): number {
	const duration = DURATIONS[state.status];
	if (duration === 0) return 0;
	return Math.max(0, duration - getElapsedMs(state));
}

export function isRunning(state: PomodoroState): boolean {
	return state.startedAt !== null && state.pausedAt === null;
}

export function isComplete(state: PomodoroState): boolean {
	if (state.status === 'idle') return false;
	return getElapsedMs(state) >= DURATIONS[state.status];
}

export function startTimer(state: PomodoroState): PomodoroState {
	const newState: PomodoroState = {
		...state,
		status: state.status === 'idle' ? 'working' : state.status,
		startedAt: Date.now(),
		pausedAt: null,
		elapsed: state.pausedAt !== null ? state.elapsed : 0
	};
	saveState(newState);
	return newState;
}

export function pauseTimer(state: PomodoroState): PomodoroState {
	if (state.startedAt === null) return state;
	const newState: PomodoroState = {
		...state,
		elapsed: state.elapsed + (Date.now() - state.startedAt),
		startedAt: null,
		pausedAt: Date.now()
	};
	saveState(newState);
	return newState;
}

export function resumeTimer(state: PomodoroState): PomodoroState {
	const newState: PomodoroState = {
		...state,
		startedAt: Date.now(),
		pausedAt: null
	};
	saveState(newState);
	return newState;
}

export function completeSegment(state: PomodoroState): PomodoroState {
	let newState: PomodoroState;

	if (state.status === 'working') {
		const completed = state.pomodorosCompleted + 1;
		if (completed >= 4) {
			newState = {
				status: 'long_break',
				startedAt: null,
				pausedAt: null,
				elapsed: 0,
				pomodorosCompleted: completed
			};
		} else {
			newState = {
				status: 'short_break',
				startedAt: null,
				pausedAt: null,
				elapsed: 0,
				pomodorosCompleted: completed
			};
		}
	} else {
		// Break finished — reset cycle if coming from long break
		const pomodorosCompleted = state.status === 'long_break' ? 0 : state.pomodorosCompleted;
		newState = {
			status: 'idle',
			startedAt: null,
			pausedAt: null,
			elapsed: 0,
			pomodorosCompleted
		};
	}

	saveState(newState);
	return newState;
}

export function resetTimer(): PomodoroState {
	const state = { ...DEFAULT_STATE };
	saveState(state);
	return state;
}

const NOTIFIED_KEY = 'anchor:timer_notified';

export function markNotified(sessionId: string): void {
	localStorage.setItem(NOTIFIED_KEY, sessionId);
}

export function wasNotified(sessionId: string): boolean {
	return localStorage.getItem(NOTIFIED_KEY) === sessionId;
}

export function getSessionId(state: PomodoroState): string {
	return `${state.status}-${state.pomodorosCompleted}-${state.elapsed}`;
}

export async function scheduleNotification(state: PomodoroState): Promise<void> {
	const base = '';

	if (!isRunning(state)) {
		try { await fetch(`${base}/api/push/schedule-timer`, { method: 'DELETE' }); } catch {}
		return;
	}

	const remaining = getRemainingMs(state);
	if (remaining <= 0) return;

	const isWork = state.status === 'working';
	const completed = state.pomodorosCompleted + (isWork ? 1 : 0);
	const fireAt = Date.now() / 1000 + remaining / 1000;

	try {
		await fetch(`${base}/api/push/schedule-timer`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				fire_at: fireAt,
				title: isWork ? 'Focus complete' : 'Break over',
				body: isWork
					? (completed >= 4 ? 'Long break time.' : 'Take a short break.')
					: 'Ready for another session.'
			})
		});
	} catch {}
}
