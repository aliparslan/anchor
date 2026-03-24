<script lang="ts">
	import {
		fetchPomodoroToday,
		fetchWeather, setWeatherZip,
		fetchVapidPublicKey, registerPushSubscription,
		fetchPreferences,
		type WeatherData
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
	import {
		Moon, Sun, X, Lightbulb, CaretDown,
		CloudSun, Cloud, CloudRain, CloudSnow, CloudLightning
	} from 'phosphor-svelte';

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

	let weather = $state<WeatherData | null>(_c?.weather ?? null);
	let weatherLocation = $state(_c?.weatherLocation ?? '');
	let weatherZip = $state<string | null>(_c?.weatherZip ?? null);
	let showZipInput = $state(_c?.showZipInput ?? false);
	let zipInput = $state('');
	let forecastExpanded = $state(
		typeof window !== 'undefined' ? localStorage.getItem('forecast_expanded') === 'true' : false
	);

	const weatherInfo: Record<number, { label: string; icon: string }> = {
		0:  { label: 'Clear',         icon: 'sun' },
		1:  { label: 'Mostly clear',  icon: 'sun' },
		2:  { label: 'Partly cloudy', icon: 'cloud-sun' },
		3:  { label: 'Overcast',      icon: 'cloud' },
		45: { label: 'Foggy',         icon: 'cloud' },
		48: { label: 'Rime fog',      icon: 'cloud' },
		51: { label: 'Light drizzle', icon: 'rain' },
		53: { label: 'Drizzle',       icon: 'rain' },
		55: { label: 'Heavy drizzle', icon: 'rain' },
		61: { label: 'Light rain',    icon: 'rain' },
		63: { label: 'Rain',          icon: 'rain' },
		65: { label: 'Heavy rain',    icon: 'rain' },
		71: { label: 'Light snow',    icon: 'snow' },
		73: { label: 'Snow',          icon: 'snow' },
		75: { label: 'Heavy snow',    icon: 'snow' },
		80: { label: 'Light showers', icon: 'rain' },
		81: { label: 'Showers',       icon: 'rain' },
		82: { label: 'Heavy showers', icon: 'rain' },
		95: { label: 'Thunderstorm',  icon: 'storm' },
		96: { label: 'Hail storm',    icon: 'storm' },
		99: { label: 'Heavy hail',    icon: 'storm' },
	};

	function getWeatherLabel(code: number): string {
		return weatherInfo[code]?.label || 'Unknown';
	}

	function getWeatherIcon(code: number): string {
		return weatherInfo[code]?.icon || 'sun';
	}

	function toggleForecast() {
		forecastExpanded = !forecastExpanded;
		if (typeof window !== 'undefined') {
			localStorage.setItem('forecast_expanded', String(forecastExpanded));
		}
	}

	async function handleSetZip() {
		if (!zipInput.trim()) return;
		const data = await setWeatherZip(zipInput.trim());
		if (data.weather) {
			weather = data.weather;
			weatherLocation = data.location;
			weatherZip = data.zip_code;
			showZipInput = false;
		}
	}

	function isNighttime(): boolean {
		const hour = new Date().getHours();
		return hour >= 19 || hour < 6;
	}

	function isHourNighttime(timeStr: string): boolean {
		const hour = new Date(timeStr).getHours();
		return hour >= 19 || hour < 6;
	}

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

	// Fetch data (skipped if restored from session cache)
	$effect(() => {
		// Always fetch preferences (not cached)
		fetchPreferences().then((prefs) => {
			userName = prefs.name;
			pomoDuration = prefs.pomo_duration;
			focusGoal = prefs.focus_goal;
		}).catch(() => {});

		if (_c) return;
		setupPushNotifications();
		fetchPomodoroToday()
			.then((pomodoro) => {
				pomodoroMinutes = pomodoro.total_minutes;
			})
			.catch((err) => { console.warn('[Home] fetch error:', err); fetchError = true; })
			.finally(() => {
				loading = false;
			});
	});

	// Save state to session cache on destroy (persists across tab switches)
	onDestroy(() => {
		setCached('home', {
			weather, weatherLocation, weatherZip, showZipInput,
			pomodoroMinutes
		});
	});

	const weatherIcon = $derived(weather ? getWeatherIcon(weather.weather_code) : 'sun');
</script>

<div class:quiet-hours={isQuietHours()}>
	{#if fetchError}
		<p class="fetch-error">Couldn't load some data</p>
	{/if}
	<PageHeader title={getGreeting()} />

	<!-- Weather widget hidden — code kept for potential re-enable -->

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
	<PomodoroTimer bind:totalMinutesToday={pomodoroMinutes} workDuration={pomoDuration} {focusGoal} />

	<SectionHeader title="Journal" style="margin-top: var(--space-section)" />
	<JournalCard />

	<Confetti trigger={showConfetti} />
</div>

<style>
	/* Weather */
	.weather-line {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-bottom: var(--space-widget);
		flex-wrap: wrap;
		font-family: var(--font-mono);
		font-size: 12px;
		font-weight: 400;
		color: var(--text-secondary);
		line-height: 2;
		row-gap: 2px;
	}

	.weather-icon {
		display: flex;
		align-items: center;
		color: var(--text-secondary);
	}

	.weather-sep {
		color: var(--text-tertiary);
	}

	.weather-rain {
		display: inline-flex;
		align-items: center;
		gap: 3px;
		color: var(--color-blue);
	}

	.weather-location {
		font-size: 12px;
		color: var(--text-tertiary);
		background: none;
		border: none;
		cursor: pointer;
		font-family: inherit;
		padding: 0;
		margin-left: 4px;
	}

	.weather-location:hover {
		color: var(--text-secondary);
	}

	.weather-zip-form {
		display: flex;
		gap: 8px;
		margin-bottom: 20px;
	}

	.weather-zip-input {
		padding: 6px 10px;
		border: 1px solid var(--border);
		border-radius: 6px;
		background: var(--bg);
		color: var(--text);
		font-family: inherit;
		font-size: 13px;
		width: 160px;
		outline: none;
	}

	.weather-zip-input:focus {
		border-color: var(--accent);
	}

	.weather-zip-btn {
		padding: 6px 14px;
		border: 1px solid var(--border);
		border-radius: 6px;
		background: var(--bg);
		color: var(--text-secondary);
		font-family: inherit;
		font-size: 13px;
		cursor: pointer;
		transition: all 0.15s ease;
	}

	.weather-zip-btn:hover {
		background: var(--bg-hover);
		color: var(--text);
		border-color: var(--text-tertiary);
	}

	/* Expandable weather forecast */
	.forecast-row {
		display: flex;
		gap: 8px;
		margin-bottom: var(--space-widget);
		animation: fadeSlideIn 0.2s ease;
	}

	.forecast-pill {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 4px;
		padding: 8px 4px;
		border-radius: 8px;
		background: var(--card-bg);
	}

	.forecast-time {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--text-tertiary);
	}

	.forecast-temp {
		font-family: var(--font-mono);
		font-size: 13px;
		font-weight: 500;
		color: var(--text);
	}

	@keyframes fadeSlideIn {
		from { opacity: 0; transform: translateY(-4px); }
		to { opacity: 1; transform: translateY(0); }
	}

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
</style>
