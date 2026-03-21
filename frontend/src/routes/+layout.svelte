<script lang="ts">
	import { page } from '$app/state';
	import { initTheme } from '$lib/theme';
	import QuickCaptureButton from '$lib/components/QuickCaptureButton.svelte';
	import SearchOverlay from '$lib/components/SearchOverlay.svelte';
	import { House, Newspaper, NotePencil, ChartBar, Pulse } from 'phosphor-svelte';
	import '../app.css';
	let { children } = $props();

	let pageReady = $state(true);
	let showSearch = $state(false);
	let captureOpen = $state(false);
	let online = $state(true);

	$effect(() => {
		online = navigator.onLine;
		const on = () => online = true;
		const off = () => online = false;
		window.addEventListener('online', on);
		window.addEventListener('offline', off);
		return () => {
			window.removeEventListener('online', on);
			window.removeEventListener('offline', off);
		};
	});

	function handleGlobalKeydown(e: KeyboardEvent) {
		if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
			e.preventDefault();
			showSearch = !showSearch;
		}
	}

	$effect(() => { initTheme(); });

	const tabs = [
		{ href: '/', label: 'Home', icon: House },
		{ href: '/feed/', label: 'Feed', icon: Newspaper },
		{ type: 'capture' as const },
		{ href: '/track/', label: 'Track', icon: ChartBar },
		{ href: '/status/', label: 'Status', icon: Pulse }
	];

	function isActive(href: string): boolean {
		if (href === '/') return page.url.pathname === '/';
		return page.url.pathname.startsWith(href);
	}
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

<SearchOverlay bind:open={showSearch} />

{#if !online}
	<div class="offline-bar">offline</div>
{/if}

<div class="app" class:page-enter={pageReady}>
	{@render children()}
</div>

<QuickCaptureButton bind:open={captureOpen} />

<nav class="bottom-nav">
	{#each tabs as tab}
		{#if 'type' in tab && tab.type === 'capture'}
			<button class="bottom-nav-capture" onclick={() => captureOpen = !captureOpen} aria-label="Quick note">
				<NotePencil size={20} weight="duotone" />
				<span>Note</span>
			</button>
		{:else if 'href' in tab}
			<a href={tab.href} class="bottom-nav-item" class:active={isActive(tab.href)}>
				<tab.icon size={20} weight="duotone" />
				<span>{tab.label}</span>
			</a>
		{/if}
	{/each}
</nav>
