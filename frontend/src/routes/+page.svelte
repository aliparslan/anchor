<script lang="ts">
	import {
		fetchPomodoroToday,
		fetchWeather, setWeatherZip,
		fetchVapidPublicKey, registerPushSubscription,
		fetchDailyStreak, fetchDailyScore,
		type WeatherData, type DailyScore
	} from '$lib/api';
	import { theme, toggleTheme } from '$lib/theme';
	import { getCached, setCached } from '$lib/cache';
	import { onDestroy } from 'svelte';
	import PomodoroTimer from '$lib/components/PomodoroTimer.svelte';
	import JournalCard from '$lib/components/JournalCard.svelte';
	import MitInput from '$lib/components/MitInput.svelte';
	import ShutdownModal from '$lib/components/ShutdownModal.svelte';
	import Confetti from '$lib/components/Confetti.svelte';
	import facts from '$lib/facts.json';
	import {
		Moon, Sun, Fire, X, Lightbulb, CaretDown,
		CloudSun, Cloud, CloudRain, CloudSnow, CloudLightning
	} from 'phosphor-svelte';

	// Restore from session cache if available (prevents re-fetch on tab switch)
	const _c = getCached<any>('home');

	let loading = $state(!_c);
	let pomodoroMinutes = $state(_c?.pomodoroMinutes ?? 0);
	let showShutdown = $state(false);
	let showConfetti = $state(false);
	let streak = $state(_c?.streak ?? 0);
	let dailyScore = $state<DailyScore | null>(_c?.dailyScore ?? null);
	let factDismissed = $state(
		typeof window !== 'undefined' && localStorage.getItem('fact_dismissed_date') === new Date().toISOString().split('T')[0]
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
		const hour = new Date().getHours();
		if (hour >= 21) return 'Wind down, Alip';
		if (hour < 12) return 'Good morning, Alip';
		if (hour < 17) return 'Good afternoon, Alip';
		return 'Good evening, Alip';
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
		typeof window !== 'undefined' && localStorage.getItem('confetti_date') === new Date().toISOString().split('T')[0]
	);
	$effect(() => {
		if (pomodoroMinutes >= 240 && !confettiShown) {
			confettiShown = true;
			showConfetti = true;
			if (typeof window !== 'undefined') {
				localStorage.setItem('confetti_date', new Date().toISOString().split('T')[0]);
			}
		}
	});

	// Fetch data (skipped if restored from session cache)
	$effect(() => {
		if (_c) return;
		setupPushNotifications();
		Promise.all([
			fetchPomodoroToday(),
			fetchWeather(),
			fetchDailyStreak(),
			fetchDailyScore()
		])
			.then(([pomodoro, weatherData, streakVal, scoreVal]) => {
				pomodoroMinutes = pomodoro.total_minutes;
				if (weatherData.weather) {
					weather = weatherData.weather;
					weatherLocation = weatherData.location;
				}
				weatherZip = weatherData.zip_code;
				if (!weatherData.zip_code) showZipInput = true;
				streak = streakVal;
				dailyScore = scoreVal;
			})
			.finally(() => {
				loading = false;
			});
	});

	// Save state to session cache on destroy (persists across tab switches)
	onDestroy(() => {
		setCached('home', {
			weather, weatherLocation, weatherZip, showZipInput,
			pomodoroMinutes, streak, dailyScore
		});
	});

	const weatherIcon = $derived(weather ? getWeatherIcon(weather.weather_code) : 'sun');
</script>

<div class:quiet-hours={isQuietHours()}>
	<div class="page-header">
		<div>
			<h1 class="greeting">{getGreeting()}</h1>
			{#if streak > 0}
				<div class="greeting-meta">
					<span class="streak"><Fire size={14} weight="duotone" /> {streak} {streak === 1 ? 'day' : 'days'}</span>
				</div>
			{/if}
		</div>
		<div class="page-header-actions">
			{#if dailyScore !== null}
				<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
				<div class="score-ring" title="{dailyScore.score}/100 — tap for details" onclick={() => showShutdown = true} style="cursor: pointer">
					<svg viewBox="0 0 36 36" class="score-ring-svg">
						<circle cx="18" cy="18" r="15.5" fill="none" stroke="var(--border)" stroke-width="3" />
						<circle cx="18" cy="18" r="15.5" fill="none" stroke="var(--accent)" stroke-width="3"
							stroke-dasharray="{dailyScore.score * 0.9749} {97.49 - dailyScore.score * 0.9749}"
							stroke-dashoffset="0" stroke-linecap="round" />
					</svg>
					<span class="score-ring-text">{dailyScore.score}</span>
				</div>
			{/if}
			<button class="theme-toggle" onclick={toggleTheme} aria-label="Toggle theme">
				{#if $theme === 'light'}
					<Moon size={18} weight="duotone" />
				{:else}
					<Sun size={18} weight="duotone" />
				{/if}
			</button>
		</div>
	</div>

	{#if loading && !weather}
		<div class="weather-line">
			<span class="skel skel-inline" style="width: 200px"></span>
		</div>
	{:else if weather}
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div class="weather-line" onclick={toggleForecast} style="cursor: pointer">
			<span class="weather-icon">
				{#if weatherIcon === 'sun'}
					{#if isNighttime()}
						<Moon size={18} weight="duotone" />
					{:else}
						<Sun size={18} weight="duotone" />
					{/if}
				{:else if weatherIcon === 'cloud-sun'}
					<CloudSun size={18} weight="duotone" />
				{:else if weatherIcon === 'cloud'}
					<Cloud size={18} weight="duotone" />
				{:else if weatherIcon === 'rain'}
					<CloudRain size={18} weight="duotone" />
				{:else if weatherIcon === 'snow'}
					<CloudSnow size={18} weight="duotone" />
				{:else if weatherIcon === 'storm'}
					<CloudLightning size={18} weight="duotone" />
				{/if}
			</span>
			<span>{weather.temp}°</span>
			<span class="weather-sep">·</span>
			<span>{getWeatherLabel(weather.weather_code)}</span>
			<span class="weather-sep">·</span>
			<span>H:{weather.high}° L:{weather.low}°</span>
			{#if weather.rain_chance > 0}
				<span class="weather-sep">·</span>
				<span class="weather-rain">
					{weather.rain_chance}% rain
				</span>
			{/if}
			<button class="weather-location" onclick={(e) => { e.stopPropagation(); showZipInput = !showZipInput; }}>{weatherLocation} <CaretDown size={10} weight="bold" /></button>
		</div>
		{#if forecastExpanded && weather?.hourly?.length > 0}
			<div class="forecast-row">
				{#each weather.hourly as hour}
					<div class="forecast-pill">
						<span class="forecast-time">
							{new Date(hour.time).toLocaleTimeString('en-US', { hour: 'numeric' })}
						</span>
						<span class="weather-icon">
							{#if hour.weather_code === 0 || hour.weather_code === 1}
								{#if isHourNighttime(hour.time)}
									<Moon size={16} weight="duotone" />
								{:else}
									<Sun size={16} weight="duotone" />
								{/if}
							{:else if hour.weather_code === 2}
								<CloudSun size={16} weight="duotone" />
							{:else if hour.weather_code === 3 || hour.weather_code === 45}
								<Cloud size={16} weight="duotone" />
							{:else if hour.weather_code === 63}
								<CloudRain size={16} weight="duotone" />
							{:else if hour.weather_code === 73}
								<CloudSnow size={16} weight="duotone" />
							{:else if hour.weather_code === 95}
								<CloudLightning size={16} weight="duotone" />
							{:else}
								{#if isHourNighttime(hour.time)}
									<Moon size={16} weight="duotone" />
								{:else}
									<Sun size={16} weight="duotone" />
								{/if}
							{/if}
						</span>
						<span class="forecast-temp">{hour.temp}°</span>
					</div>
				{/each}
			</div>
		{/if}
	{:else if showZipInput}
		<div class="weather-line">
			<span>Set your location:</span>
		</div>
	{/if}
	{#if showZipInput}
		<form class="weather-zip-form" onsubmit={(e) => { e.preventDefault(); handleSetZip(); }}>
			<input class="weather-zip-input" type="text" bind:value={zipInput} placeholder="City or zip code" />
			<button class="weather-zip-btn" type="submit">Set</button>
		</form>
	{/if}

	{#if !factDismissed}
		<div class="fact-card">
			<Lightbulb size={14} weight="duotone" class="fact-icon" />
			<span class="fact-text">{dailyFact}</span>
			<button class="fact-dismiss" onclick={() => {
				factDismissed = true;
				localStorage.setItem('fact_dismissed_date', new Date().toISOString().split('T')[0]);
			}} aria-label="Dismiss">
				<X size={12} weight="bold" />
			</button>
		</div>
	{/if}

	<MitInput />

	<div class="home-top">
		<PomodoroTimer bind:totalMinutesToday={pomodoroMinutes} />
	</div>

	<JournalCard />

	<ShutdownModal open={showShutdown} onclose={() => { showShutdown = false; fetchDailyScore().then(s => dailyScore = s); }} />
	<Confetti trigger={showConfetti} />
</div>
