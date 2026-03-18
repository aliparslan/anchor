import { writable } from 'svelte/store';

export type Theme = 'light' | 'dark';

const themeStore = writable<Theme>('light');

export const theme = { subscribe: themeStore.subscribe };

function applySeason() {
	if (typeof window === 'undefined') return;
	const month = new Date().getMonth(); // 0-11
	let season: string;
	if (month >= 2 && month <= 4) season = 'spring';
	else if (month >= 5 && month <= 7) season = 'summer';
	else if (month >= 8 && month <= 10) season = 'autumn';
	else season = 'winter';
	document.documentElement.setAttribute('data-season', season);
}

export function initTheme() {
	if (typeof window === 'undefined') return;
	const saved = localStorage.getItem('theme');
	const value: Theme =
		saved === 'dark' ? 'dark' :
		saved === 'light' ? 'light' :
		window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
	themeStore.set(value);
	document.documentElement.setAttribute('data-theme', value);
	applySeason();
}

export function toggleTheme() {
	themeStore.update((t) => {
		const next: Theme = t === 'light' ? 'dark' : 'light';
		document.documentElement.setAttribute('data-theme', next);
		localStorage.setItem('theme', next);
		return next;
	});
}
