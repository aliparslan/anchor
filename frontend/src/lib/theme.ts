import { writable } from 'svelte/store';

export type Theme = 'light' | 'dark';

const themeStore = writable<Theme>('light');

export const theme = { subscribe: themeStore.subscribe };

export function initTheme() {
	if (typeof window === 'undefined') return;
	const saved = localStorage.getItem('theme');
	const value: Theme =
		saved === 'dark' ? 'dark' :
		saved === 'light' ? 'light' :
		window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
	themeStore.set(value);
	document.documentElement.setAttribute('data-theme', value);
}

export function toggleTheme() {
	themeStore.update((t) => {
		const next: Theme = t === 'light' ? 'dark' : 'light';
		document.documentElement.setAttribute('data-theme', next);
		localStorage.setItem('theme', next);
		return next;
	});
}
