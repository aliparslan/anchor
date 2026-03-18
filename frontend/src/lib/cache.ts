/** Simple in-memory cache that persists across SvelteKit navigations within a session. */
const store = new Map<string, any>();

export function getCached<T>(key: string): T | undefined {
	return store.get(key) as T | undefined;
}

export function setCached(key: string, value: any): void {
	store.set(key, value);
}

export function clearCached(key: string): void {
	store.delete(key);
}
