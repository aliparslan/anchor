<script lang="ts">
	import { page } from '$app/state';
	import { initTheme } from '$lib/theme';
	import QuickCaptureButton from '$lib/components/QuickCaptureButton.svelte';
	import '../app.css';
	let { children } = $props();

	$effect(() => { initTheme(); });
</script>

<div class="app">
	{@render children()}
</div>

<QuickCaptureButton />

<nav class="bottom-nav">
	<a href="/" class="bottom-nav-item" class:active={page.url.pathname === '/'}>
		<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
			<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
		</svg>
		<span>Home</span>
	</a>
	<a href="/track" class="bottom-nav-item" class:active={page.url.pathname === '/track'}>
		<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
			<polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
		</svg>
		<span>Track</span>
	</a>
	<a href="/inbox" class="bottom-nav-item" class:active={page.url.pathname === '/inbox'}>
		<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
			<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
		</svg>
		<span>Inbox</span>
	</a>
</nav>
