<script lang="ts">
	import {
		fetchSystemStatus, fetchClaudeStatus, fetchTailscaleStatus,
		fetchDashboardAge,
		type SystemStatus, type ClaudeStatus, type TailscaleStatus
	} from '$lib/api';
	import { getCached, setCached } from '$lib/cache';
	import { theme, toggleTheme } from '$lib/theme';
	import { Desktop, Robot, Globe, Moon, Sun, Circle } from 'phosphor-svelte';
	import { onDestroy } from 'svelte';

	const _c = getCached<any>('status');
	let system = $state<SystemStatus | null>(_c?.system ?? null);
	let claude = $state<ClaudeStatus | null>(_c?.claude ?? null);
	let tailscale = $state<TailscaleStatus | null>(_c?.tailscale ?? null);
	let dashboardAge = $state<{ days: number; since: string } | null>(_c?.dashboardAge ?? null);

	onDestroy(() => {
		setCached('status', { system, claude, tailscale, dashboardAge });
	});

	function formatTokens(n: number): string {
		if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
		if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
		return String(n);
	}

	async function refresh() {
		const [s, c, t, age] = await Promise.all([
			fetchSystemStatus().catch(() => null),
			fetchClaudeStatus().catch(() => null),
			fetchTailscaleStatus().catch(() => null),
			fetchDashboardAge().catch(() => null),
		]);
		if (s) system = s;
		if (c) claude = c;
		if (t) tailscale = t;
		if (age) dashboardAge = age;
	}

	$effect(() => {
		refresh();
		const interval = setInterval(refresh, 30000);
		return () => clearInterval(interval);
	});
</script>

<div class="page-header">
	<h1 class="greeting">Status</h1>
	<button class="theme-toggle" onclick={toggleTheme} aria-label="Toggle theme">
		{#if $theme === 'light'}
			<Moon size={18} weight="duotone" />
		{:else}
			<Sun size={18} weight="duotone" />
		{/if}
	</button>
</div>

<!-- System -->
<div class="home-section">
	<div class="section-header">
		<span class="section-title">System</span>
	</div>
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

<!-- Claude -->
<div class="home-section">
	<div class="section-header">
		<span class="section-title">Claude</span>
	</div>
	{#if claude?.available}
		<div class="status-card">
			<div class="status-card-header">
				<Robot size={18} weight="duotone" />
				<span class="status-card-name">Claude Code</span>
				{#if claude.last_computed}
					<span class="status-card-meta">as of {claude.last_computed}</span>
				{/if}
			</div>
			<div class="status-stats">
				<div class="status-stat">
					<span class="status-stat-value">{claude.total_messages?.toLocaleString()}</span>
					<span class="status-stat-label">Messages</span>
				</div>
				<div class="status-stat">
					<span class="status-stat-value">{claude.total_sessions}</span>
					<span class="status-stat-label">Sessions</span>
				</div>
			</div>
			{#if claude.model_usage}
				<div class="status-model-list">
					{#each Object.entries(claude.model_usage) as [model, usage]}
						<div class="status-model-row">
							<span class="status-model-name">{model.replace('claude-', '').replace(/-\d+$/, '')}</span>
							<span class="status-model-tokens">
								{formatTokens(usage.inputTokens + usage.outputTokens + (usage.cacheReadInputTokens || 0) + (usage.cacheCreationInputTokens || 0))} tokens
							</span>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{:else}
		<div class="empty">Claude stats not available</div>
	{/if}
</div>

<!-- Tailscale -->
<div class="home-section">
	<div class="section-header">
		<span class="section-title">Network</span>
	</div>
	{#if tailscale?.available}
		<div class="status-card">
			<div class="status-card-header">
				<Globe size={18} weight="duotone" />
				<span class="status-card-name">Tailscale</span>
			</div>
			<div class="status-device-list">
				{#if tailscale.self}
					<div class="status-device-row">
						<Circle size={8} weight="fill" color="#22c55e" />
						<span class="status-device-name">{tailscale.self.hostname}</span>
						<span class="status-device-meta">this device · {tailscale.self.ip}</span>
					</div>
				{/if}
				{#each tailscale.peers ?? [] as peer}
					<div class="status-device-row">
						<Circle size={8} weight="fill" color={peer.online ? '#22c55e' : 'var(--text-tertiary)'} />
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
	.status-card {
		border-radius: 10px;
		padding: 16px;
		background: var(--card-bg);
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
		border-radius: 3px;
		background: var(--bg-inset);
		overflow: hidden;
	}

	.status-bar-fill {
		height: 100%;
		border-radius: 3px;
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

	.status-stats {
		display: flex;
		gap: 24px;
		margin-bottom: 14px;
	}

	.status-stat {
		text-align: center;
	}

	.status-stat-value {
		display: block;
		font-family: var(--font-mono);
		font-size: 18px;
		color: var(--text);
	}

	.status-stat-label {
		font-family: var(--font-display);
		font-size: 11px;
		color: var(--text-tertiary);
	}

	.status-model-list {
		display: flex;
		flex-direction: column;
		gap: 6px;
		padding-top: 12px;
		border-top: 1px solid var(--border);
	}

	.status-model-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.status-model-name {
		font-family: var(--font-mono);
		font-size: 12px;
		color: var(--text-secondary);
	}

	.status-model-tokens {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--text-tertiary);
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
