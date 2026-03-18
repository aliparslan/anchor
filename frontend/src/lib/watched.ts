const WATCHED_KEY = 'base:watched_videos';
const READ_HN_KEY = 'base:read_hn';

function getSet(key: string): Set<string> {
	try {
		const data = localStorage.getItem(key);
		return data ? new Set(JSON.parse(data)) : new Set();
	} catch {
		return new Set();
	}
}

function saveSet(key: string, set: Set<string>) {
	localStorage.setItem(key, JSON.stringify([...set]));
}

export function isWatched(videoId: string): boolean {
	return getSet(WATCHED_KEY).has(videoId);
}

export function markWatched(videoId: string) {
	const set = getSet(WATCHED_KEY);
	set.add(videoId);
	saveSet(WATCHED_KEY, set);
}

export function isHnRead(hnId: string): boolean {
	return getSet(READ_HN_KEY).has(hnId);
}

export function markHnRead(hnId: string) {
	const set = getSet(READ_HN_KEY);
	set.add(hnId);
	saveSet(READ_HN_KEY, set);
}
