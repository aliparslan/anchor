<script lang="ts">
	import { page } from '$app/state';
	import { afterNavigate } from '$app/navigation';
	import { initTheme } from '$lib/theme';
	import QuickCaptureButton from '$lib/components/QuickCaptureButton.svelte';
	import SearchOverlay from '$lib/components/SearchOverlay.svelte';
	import { House, Newspaper, ChartBar, Tray, Pulse } from 'phosphor-svelte';
	import '../app.css';
	let { children } = $props();

	let pageReady = $state(true);

	afterNavigate(() => {
		pageReady = false;
		requestAnimationFrame(() => { pageReady = true; });
	});

	let showSearch = $state(false);

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
		{ href: '/track/', label: 'Track', icon: ChartBar },
		{ href: '/inbox/', label: 'Inbox', icon: Tray },
		{ href: '/status/', label: 'Status', icon: Pulse }
	];

	function isActive(href: string): boolean {
		if (href === '/') return page.url.pathname === '/';
		return page.url.pathname.startsWith(href);
	}
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

<SearchOverlay bind:open={showSearch} />

<div class="app" class:page-enter={pageReady}>
	{@render children()}
</div>

<QuickCaptureButton />

<nav class="bottom-nav">
	{#each tabs as tab}
		<a href={tab.href} class="bottom-nav-item" class:active={isActive(tab.href)}>
			<tab.icon size={20} weight="duotone" />
			<span>{tab.label}</span>
		</a>
	{/each}
</nav>
