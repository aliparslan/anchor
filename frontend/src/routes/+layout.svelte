<script lang="ts">
	import { page } from '$app/state';
	import { onNavigate } from '$app/navigation';
	import { fade } from 'svelte/transition';
	import { initTheme } from '$lib/theme';
	import QuickCaptureButton from '$lib/components/QuickCaptureButton.svelte';
	import SearchOverlay from '$lib/components/SearchOverlay.svelte';
	import ToastContainer from '$lib/components/ToastContainer.svelte';
	import { House, Newspaper, NotePencil, ChartBar, ListChecks } from 'phosphor-svelte';
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
	$effect(() => { page.url.pathname; captureOpen = false; });

	onNavigate((navigation) => {
		if (!document.startViewTransition) return;
		return new Promise((resolve) => {
			document.startViewTransition(async () => {
				resolve();
				await navigation.complete;
			});
		});
	});

	const tabs = [
		{ href: '/', label: 'Home', icon: House },
		{ href: '/feed/', label: 'Feed', icon: Newspaper },
		{ type: 'capture' as const },
		{ href: '/todos/', label: 'Todos', icon: ListChecks },
		{ href: '/track/', label: 'Track', icon: ChartBar },
	];

	function isActive(href: string): boolean {
		if (href === '/') return page.url.pathname === '/';
		return page.url.pathname.startsWith(href);
	}
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

<SearchOverlay bind:open={showSearch} />

{#if !online}
	<div class="offline-bar">You're offline — cached data may be stale</div>
{/if}

<ToastContainer />

<div class="app">
	{#key page.url.pathname}
		<div in:fade={{ duration: 100, delay: 30 }} out:fade={{ duration: 60 }}>
			{@render children()}
		</div>
	{/key}
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
