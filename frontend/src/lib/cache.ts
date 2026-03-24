/** Simple in-memory cache that persists across SvelteKit navigations within a session. */

interface CacheEntry {
	value: any;
	timestamp: number;
}

const store = new Map<string, CacheEntry>();

/** Default max age: 60 seconds. Prevents showing stale data when navigating back to a page. */
const DEFAULT_MAX_AGE = 60_000;

export function getCached<T>(key: string, maxAge = DEFAULT_MAX_AGE): T | undefined {
	const entry = store.get(key);
	if (!entry) return undefined;
	if (Date.now() - entry.timestamp > maxAge) {
		store.delete(key);
		return undefined;
	}
	return entry.value as T;
}

export function setCached(key: string, value: any): void {
	store.set(key, { value, timestamp: Date.now() });
}

export function clearCached(key: string): void {
	store.delete(key);
}
