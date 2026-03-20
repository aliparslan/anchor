import { fetchDailyScore, type DailyScore } from '$lib/api';

let score: DailyScore | null = null;
let fetched = false;
let listeners: Array<(s: DailyScore | null) => void> = [];

export function getScore(): DailyScore | null {
	if (!fetched) {
		fetched = true;
		refreshScore();
	}
	return score;
}

export async function refreshScore(): Promise<DailyScore | null> {
	try {
		score = await fetchDailyScore();
	} catch {
		// silent fail
	}
	listeners.forEach((fn) => fn(score));
	return score;
}

export function onScoreChange(fn: (s: DailyScore | null) => void): () => void {
	listeners.push(fn);
	return () => {
		listeners = listeners.filter((l) => l !== fn);
	};
}
