const WATCHED_KEY = 'base:watched_videos';
const READ_HN_KEY = 'base:read_hn';

let watchedCache: Set<string> | null = null;
let readHnCache: Set<string> | null = null;

function loadSet(key: string): Set<string> {
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
	if (!watchedCache) watchedCache = loadSet(WATCHED_KEY);
	return watchedCache.has(videoId);
}

export function markWatched(videoId: string) {
	if (!watchedCache) watchedCache = loadSet(WATCHED_KEY);
	watchedCache.add(videoId);
	saveSet(WATCHED_KEY, watchedCache);
}

export function isHnRead(hnId: string): boolean {
	if (!readHnCache) readHnCache = loadSet(READ_HN_KEY);
	return readHnCache.has(hnId);
}

export function markHnRead(hnId: string) {
	if (!readHnCache) readHnCache = loadSet(READ_HN_KEY);
	readHnCache.add(hnId);
	saveSet(READ_HN_KEY, readHnCache);
}
