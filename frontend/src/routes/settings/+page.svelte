<script lang="ts">
	import {
		fetchSystemStatus, fetchTailscaleStatus,
		fetchDashboardAge,
		fetchPreferences, savePreferences,
		fetchFeedConfigs, addFeedConfig, deleteFeedConfig,
		type SystemStatus, type TailscaleStatus, type RssFeedConfig
	} from '$lib/api';
	import { getCached, setCached } from '$lib/cache';
	import { Desktop, Globe, Circle, X, Plus } from 'phosphor-svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SectionHeader from '$lib/components/SectionHeader.svelte';
	import { onDestroy } from 'svelte';

	const _c = getCached<any>('status');
	let system = $state<SystemStatus | null>(_c?.system ?? null);
	let tailscale = $state<TailscaleStatus | null>(_c?.tailscale ?? null);
	let dashboardAge = $state<{ days: number; since: string } | null>(_c?.dashboardAge ?? null);

	// Preferences
	let prefName = $state('');
	let pomoDuration = $state(25);
	let focusGoal = $state(120);
	let prefSaved = $state(false);
	let prefSavedTimeout: ReturnType<typeof setTimeout> | null = null;

	// RSS Feeds
	let feeds = $state<RssFeedConfig[]>([]);
	let newFeedName = $state('');
	let newFeedUrl = $state('');
	let newFeedSiteUrl = $state('');

	onDestroy(() => {
		setCached('status', { system, tailscale, dashboardAge });
		if (prefSavedTimeout) clearTimeout(prefSavedTimeout);
	});

	async function refresh() {
		const [s, t, age] = await Promise.all([
			fetchSystemStatus().catch(() => null),
			fetchTailscaleStatus().catch(() => null),
			fetchDashboardAge().catch(() => null),
		]);
		if (s) system = s;
		if (t) tailscale = t;
		if (age) dashboardAge = age;
	}

	async function loadPreferences() {
		try {
			const prefs = await fetchPreferences();
			prefName = prefs.name;
			pomoDuration = prefs.pomo_duration;
			focusGoal = prefs.focus_goal;
		} catch { /* no-op */ }
	}

	async function loadFeeds() {
		try {
			feeds = await fetchFeedConfigs();
		} catch { /* no-op */ }
	}

	function flashSaved() {
		prefSaved = true;
		if (prefSavedTimeout) clearTimeout(prefSavedTimeout);
		prefSavedTimeout = setTimeout(() => { prefSaved = false; }, 2000);
	}

	async function handlePrefBlur() {
		try {
			await savePreferences({ name: prefName, pomo_duration: pomoDuration, focus_goal: focusGoal });
			flashSaved();
		} catch { /* no-op */ }
	}

	async function handleAddFeed() {
		if (!newFeedName.trim() || !newFeedUrl.trim()) return;
		try {
			const added = await addFeedConfig({ name: newFeedName.trim(), feed_url: newFeedUrl.trim(), site_url: newFeedSiteUrl.trim() });
			feeds = [...feeds, added];
			newFeedName = '';
			newFeedUrl = '';
			newFeedSiteUrl = '';
		} catch { /* no-op */ }
	}

	async function handleDeleteFeed(id: number) {
		try {
			await deleteFeedConfig(id);
			feeds = feeds.filter(f => f.id !== id);
		} catch { /* no-op */ }
	}

	$effect(() => {
		refresh();
		loadPreferences();
		loadFeeds();
		const interval = setInterval(refresh, 30000);
		return () => clearInterval(interval);
	});
</script>

<PageHeader title="Settings" />

<!-- Preferences -->
<div class="home-section">
	<SectionHeader title="Preferences">
		{#if prefSaved}
			<span class="saved-indicator">Saved</span>
		{/if}
	</SectionHeader>
	<div class="pref-card">
		<div class="pref-row">
			<label class="pref-label" for="pref-name">Name</label>
			<div class="pref-input-group">
				<input id="pref-name" class="pref-input" type="text" bind:value={prefName} onblur={handlePrefBlur} />
				<span class="pref-suffix pref-suffix-hidden">min</span>
			</div>
		</div>
		<div class="pref-row">
			<label class="pref-label" for="pref-pomo">Pomodoro</label>
			<div class="pref-input-group">
				<input id="pref-pomo" class="pref-input pref-input-num" type="number" min="1" max="120" bind:value={pomoDuration} onblur={handlePrefBlur} />
				<span class="pref-suffix">min</span>
			</div>
		</div>
		<div class="pref-row">
			<label class="pref-label" for="pref-focus">Focus goal</label>
			<div class="pref-input-group">
				<input id="pref-focus" class="pref-input pref-input-num" type="number" min="1" max="720" bind:value={focusGoal} onblur={handlePrefBlur} />
				<span class="pref-suffix">min</span>
			</div>
		</div>
	</div>
</div>

<!-- RSS Feeds -->
<div class="home-section">
	<SectionHeader title="RSS Feeds" />
	<div class="feed-card">
		{#if feeds.length > 0}
			<div class="feed-list">
				{#each feeds as feed (feed.id)}
					<div class="feed-row">
						<div class="feed-info">
							<span class="feed-name">{feed.name}</span>
							<span class="feed-url">{feed.feed_url}</span>
						</div>
						<button class="feed-delete" onclick={() => handleDeleteFeed(feed.id)} aria-label="Remove {feed.name}">
							<X size={14} weight="bold" />
						</button>
					</div>
				{/each}
			</div>
		{:else}
			<div class="feed-empty">No feeds configured</div>
		{/if}
		<form class="feed-add-form" onsubmit={(e) => { e.preventDefault(); handleAddFeed(); }}>
			<input class="feed-add-input" type="text" placeholder="Feed name" bind:value={newFeedName} />
			<input class="feed-add-input" type="url" placeholder="Feed URL" bind:value={newFeedUrl} />
			<input class="feed-add-input" type="url" placeholder="Site URL (optional)" bind:value={newFeedSiteUrl} />
			<button type="submit" class="feed-add-btn" disabled={!newFeedName.trim() || !newFeedUrl.trim()}>
				<Plus size={14} weight="bold" />
				Add
			</button>
		</form>
	</div>
</div>

<!-- System -->
<div class="home-section">
	<SectionHeader title="System" />
	{#if system}
		<div class="status-card">
			<div class="status-card-header">
				<Desktop size={18} weight="duotone" />
				<span class="status-card-name">{system.hostname}</span>
				<span class="status-card-meta">up {system.uptime}</span>
			</div>
			<div class="status-bars">
				<div class="status-bar-row">
					<span class="status-bar-label">CPU</span>
					<div class="status-bar-track">
						<div class="status-bar-fill" style="width: {system.cpu_percent}%"></div>
					</div>
					<span class="status-bar-value">{system.cpu_percent}%</span>
				</div>
				<div class="status-bar-row">
					<span class="status-bar-label">RAM</span>
					<div class="status-bar-track">
						<div class="status-bar-fill" style="width: {system.memory.percent}%"></div>
					</div>
					<span class="status-bar-value">{system.memory.used_gb}/{system.memory.total_gb} GB</span>
				</div>
				<div class="status-bar-row">
					<span class="status-bar-label">Disk</span>
					<div class="status-bar-track">
						<div class="status-bar-fill" style="width: {system.disk.percent}%"></div>
					</div>
					<span class="status-bar-value">{system.disk.used_gb}/{system.disk.total_gb} GB</span>
				</div>
			</div>
		</div>
	{:else}
		<div class="empty">Loading...</div>
	{/if}
</div>

<!-- Tailscale -->
<div class="home-section">
	<SectionHeader title="Network" />
	{#if tailscale?.available}
		<div class="status-card">
			<div class="status-card-header">
				<Globe size={18} weight="duotone" />
				<span class="status-card-name">Tailscale</span>
			</div>
			<div class="status-device-list">
				{#if tailscale.self}
					<div class="status-device-row">
						<Circle size={8} weight="fill" color="var(--color-green)" />
						<span class="status-device-name">{tailscale.self.hostname}</span>
						<span class="status-device-meta">this device · {tailscale.self.ip}</span>
					</div>
				{/if}
				{#each tailscale.peers ?? [] as peer}
					<div class="status-device-row">
						<Circle size={8} weight="fill" color={peer.online ? 'var(--color-green)' : 'var(--text-tertiary)'} />
						<span class="status-device-name">{peer.hostname}</span>
						<span class="status-device-meta">{peer.os}{peer.online ? ` · ${peer.ip}` : ' · offline'}</span>
					</div>
				{/each}
			</div>
		</div>
	{:else}
		<div class="empty">Tailscale not available</div>
	{/if}
</div>


{#if dashboardAge}
	<div class="dashboard-age">
		This dashboard has been alive for {dashboardAge.days} {dashboardAge.days === 1 ? 'day' : 'days'}
	</div>
{/if}

<style>
	.pref-card {
		border-radius: var(--radius-md);
		background: var(--card-bg);
		border: 1px solid var(--border);
		padding: 4px 0;
	}

	.pref-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-md);
		padding: 14px 14px;
		border-bottom: 1px solid var(--border);
	}

	.pref-row:last-child {
		border-bottom: none;
	}

	.pref-label {
		font-family: var(--font-sans);
		font-size: 14px;
		color: var(--text);
		flex-shrink: 0;
	}

	.pref-input {
		border: none;
		background: none;
		color: var(--text-secondary);
		font-family: var(--font-mono);
		font-size: 14px;
		outline: none;
		text-align: right;
		min-width: 0;
	}

	.pref-input-group {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: 4px;
	}

	.pref-input-num {
		width: 56px;
		text-align: right;
		-moz-appearance: textfield;
	}

	.pref-input-num::-webkit-inner-spin-button,
	.pref-input-num::-webkit-outer-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}

	.pref-suffix {
		font-family: var(--font-mono);
		font-size: 12px;
		color: var(--text-tertiary);
	}

	.pref-suffix-hidden {
		visibility: hidden;
	}

	.saved-indicator {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--text-tertiary);
	}

	.feed-card {
		border-radius: var(--radius-md);
		background: var(--card-bg);
		border: 1px solid var(--border);
		padding: 4px 0;
	}

	.feed-list {
		display: flex;
		flex-direction: column;
	}

	.feed-row {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 14px 14px;
		border-bottom: 1px solid var(--border);
	}

	.feed-row:last-child {
		border-bottom: none;
	}

	.feed-info {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.feed-name {
		font-family: var(--font-display);
		font-size: 13px;
		font-weight: 500;
		color: var(--text);
	}

	.feed-url {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--text-tertiary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.feed-delete {
		background: none;
		border: none;
		color: var(--text-tertiary);
		cursor: pointer;
		padding: 4px;
		border-radius: var(--radius-sm);
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.feed-delete:hover {
		color: var(--text);
	}

	.feed-empty {
		font-family: var(--font-mono);
		font-size: 12px;
		color: var(--text-tertiary);
		padding: 8px 14px;
	}

	.feed-add-form {
		display: flex;
		flex-direction: column;
		gap: 8px;
		padding: 12px 14px 14px;
		border-top: 1px solid var(--border);
	}

	.feed-add-input {
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: 8px 10px;
		background: var(--bg-inset);
		color: var(--text);
		font-family: var(--font-sans);
		font-size: 13px;
		outline: none;
	}

	.feed-add-input:focus {
		border-color: var(--accent);
	}

	.feed-add-input::placeholder {
		color: var(--text-tertiary);
	}

	.feed-add-btn {
		align-self: flex-end;
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 6px 12px;
		border: none;
		border-radius: var(--radius-sm);
		background: var(--accent);
		color: var(--bg);
		font-family: var(--font-sans);
		font-size: 12px;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.15s ease;
	}

	.feed-add-btn:disabled {
		opacity: 0.4;
		cursor: default;
	}

	/* System */
	.status-card {
		border-radius: var(--radius-md);
		padding: var(--space-lg);
		background: var(--card-bg);
		border: 1px solid var(--border);
	}

	.status-card-header {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 14px;
		color: var(--text-secondary);
	}

	.status-card-name {
		font-family: var(--font-display);
		font-size: 13px;
		font-weight: 600;
		color: var(--text);
	}

	.status-card-meta {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--text-tertiary);
		margin-left: auto;
	}

	.status-bars {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.status-bar-row {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.status-bar-label {
		font-family: var(--font-mono);
		font-size: 10px;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--text-tertiary);
		width: 32px;
	}

	.status-bar-track {
		flex: 1;
		height: 6px;
		border-radius: var(--radius-sm);
		background: var(--bg-inset);
		overflow: hidden;
	}

	.status-bar-fill {
		height: 100%;
		border-radius: var(--radius-sm);
		background: linear-gradient(90deg, var(--accent), color-mix(in srgb, var(--accent) 70%, white));
		transition: width 0.5s ease;
	}

	.status-bar-value {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--text-secondary);
		min-width: 70px;
		text-align: right;
	}

	.status-device-list {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.status-device-row {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.status-device-name {
		font-family: var(--font-display);
		font-size: 13px;
		font-weight: 500;
		color: var(--text);
	}

	.status-device-meta {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--text-tertiary);
		margin-left: auto;
	}

	.dashboard-age {
		text-align: center;
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--text-tertiary);
		padding: 24px 0 8px;
	}
</style>
