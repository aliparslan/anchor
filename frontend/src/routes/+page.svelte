<script lang="ts">
	import {
		fetchPomodoroToday,
		fetchVapidPublicKey, registerPushSubscription,
		fetchPreferences,
		} from '$lib/api';
	import { getCached, setCached } from '$lib/cache';
	import { onDestroy } from 'svelte';
	import PomodoroTimer from '$lib/components/PomodoroTimer.svelte';
	import JournalCard from '$lib/components/JournalCard.svelte';
	import MitInput from '$lib/components/MitInput.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SectionHeader from '$lib/components/SectionHeader.svelte';
	import Confetti from '$lib/components/Confetti.svelte';
	import facts from '$lib/facts.json';
	import { localDate } from '$lib/utils';
	import { X, Lightbulb } from 'phosphor-svelte';

	// Restore from session cache if available (prevents re-fetch on tab switch)
	const _c = getCached<any>('home');

	let loading = $state(!_c);
	let fetchError = $state(false);
	let pomodoroMinutes = $state(_c?.pomodoroMinutes ?? 0);
	let showConfetti = $state(false);
	let userName = $state('');
	let pomoDuration = $state(25);
	let focusGoal = $state(240);
	let factDismissed = $state(
		typeof window !== 'undefined' && localStorage.getItem('fact_dismissed_date') === localDate()
	);

	const dayOfYear = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0).getTime()) / 86400000);
	const dailyFact = facts[dayOfYear % facts.length];


	function isQuietHours(): boolean {
		return new Date().getHours() >= 21;
	}

	function getGreeting(): string {
		const name = userName || 'there';
		const hour = new Date().getHours();
		if (hour >= 21) return `Wind down, ${name}`;
		if (hour < 12) return `Good morning, ${name}`;
		if (hour < 17) return `Good afternoon, ${name}`;
		return `Good evening, ${name}`;
	}

	async function setupPushNotifications() {
		if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
		if (Notification.permission !== 'granted') return;
		try {
			const reg = await navigator.serviceWorker.ready;
			const existing = await reg.pushManager.getSubscription();
			if (existing) return;
			const publicKey = await fetchVapidPublicKey();
			const keyBytes = Uint8Array.from(
				atob(publicKey.replace(/-/g, '+').replace(/_/g, '/')),
				(c) => c.charCodeAt(0)
			);
			const sub = await reg.pushManager.subscribe({
				userVisibleOnly: true,
				applicationServerKey: keyBytes
			});
			await registerPushSubscription(sub.toJSON() as PushSubscriptionJSON);
		} catch (e) {
			console.warn('[Push] subscription failed:', e);
		}
	}

	let confettiShown = $state(
		typeof window !== 'undefined' && localStorage.getItem('confetti_date') === localDate()
	);
	$effect(() => {
		if (pomodoroMinutes >= 240 && !confettiShown) {
			confettiShown = true;
			showConfetti = true;
			if (typeof window !== 'undefined') {
				localStorage.setItem('confetti_date', localDate());
			}
		}
	});

	function doFetch() {
		loading = true;
		fetchError = false;
		fetchPreferences().then((prefs) => {
			userName = prefs.name;
			pomoDuration = prefs.pomo_duration;
			focusGoal = prefs.focus_goal;
		}).catch(() => {});

		setupPushNotifications();
		fetchPomodoroToday()
			.then((pomodoro) => {
				pomodoroMinutes = pomodoro.total_minutes;
			})
			.catch((err) => { console.warn('[Home] fetch error:', err); fetchError = true; })
			.finally(() => {
				loading = false;
			});
	}

	function retryFetch() {
		doFetch();
	}

	// Fetch data (skipped if restored from session cache)
	$effect(() => {
		if (_c) {
			// Always fetch preferences even from cache
			fetchPreferences().then((prefs) => {
				userName = prefs.name;
				pomoDuration = prefs.pomo_duration;
				focusGoal = prefs.focus_goal;
			}).catch(() => {});
			return;
		}
		doFetch();
	});

	// Save state to session cache on destroy (persists across tab switches)
	onDestroy(() => {
		setCached('home', {
			pomodoroMinutes
		});
	});

</script>

<div class:quiet-hours={isQuietHours()}>
	{#if fetchError}
		<p class="fetch-error">Couldn't load some data · <button class="retry-btn" onclick={retryFetch}>Retry</button></p>
	{/if}
	<PageHeader title={getGreeting()} />

	{#if !factDismissed}
		<div class="fact-card">
			<Lightbulb size={20} weight="duotone" class="fact-icon" />
			<span class="fact-text">{dailyFact}</span>
			<button class="fact-dismiss" onclick={() => {
				factDismissed = true;
				localStorage.setItem('fact_dismissed_date', localDate());
			}} aria-label="Dismiss">
				<X size={12} weight="bold" />
			</button>
		</div>
	{/if}

	<SectionHeader title="Priority" />
	<MitInput />

	<SectionHeader title="Focus" style="margin-top: var(--space-section)" />
	{#if loading}
		<div class="skel-pomo">
			<div class="skel skel-line" style="width: 60%; height: 48px; margin: 0 auto 12px"></div>
			<div class="skel skel-line" style="width: 40%; height: 14px; margin: 0 auto"></div>
		</div>
	{:else}
		<PomodoroTimer bind:totalMinutesToday={pomodoroMinutes} workDuration={pomoDuration} {focusGoal} />
	{/if}

	<SectionHeader title="Journal" style="margin-top: var(--space-section)" />
	<JournalCard />

	<Confetti trigger={showConfetti} />
</div>

<style>
	/* Daily fact card */
	.fact-card {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 14px;
		margin-bottom: var(--space-widget);
		border-radius: 8px;
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		font-family: var(--font-sans);
		font-size: 13px;
		color: var(--text-secondary);
		line-height: 1.5;
	}

	:global(.fact-icon) {
		flex-shrink: 0;
		color: var(--text-tertiary);
	}

	.fact-text {
		flex: 1;
	}

	.fact-dismiss {
		flex-shrink: 0;
		width: 36px;
		height: 36px;
		border: none;
		background: none;
		color: var(--text-tertiary);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0;
		border-radius: 4px;
		transition: all 0.15s ease;
	}

	.fact-dismiss:hover {
		background: var(--bg-hover);
		color: var(--text);
	}

	.skel-pomo {
		border-radius: var(--radius-lg);
		background: var(--card-bg);
		border: 1px solid var(--border);
		padding: 40px var(--space-lg);
		margin-bottom: var(--space-widget);
		text-align: center;
	}
</style>
