<script lang="ts">
	import {
		fetchHnPosts, fetchYoutubeVideos, fetchPomodoroToday,
		refreshHn, refreshYoutube,
		fetchWeather, setWeatherZip,
		fetchVapidPublicKey, registerPushSubscription,
		fetchDismissedVideoIds, dismissVideoServer,
		saveToReadingQueue,
		type HnPost, type YoutubeVideo, type WeatherData
	} from '$lib/api';
	import { isWatched, markWatched, isHnRead, markHnRead } from '$lib/watched';
	import { theme, toggleTheme } from '$lib/theme';
	import VideoPlayer from '$lib/components/VideoPlayer.svelte';
	import PomodoroTimer from '$lib/components/PomodoroTimer.svelte';
	import JournalCard from '$lib/components/JournalCard.svelte';
	import MitInput from '$lib/components/MitInput.svelte';
	import ShutdownModal from '$lib/components/ShutdownModal.svelte';
	import Confetti from '$lib/components/Confetti.svelte';

	let hnPosts = $state<HnPost[]>([]);
	let ytVideos = $state<YoutubeVideo[]>([]);
	let loading = $state(true);
	let activeVideoId = $state('');
	let watchedSet = $state(new Set<string>());
	let dismissedSet = $state(new Set<string>()); // server-sourced
	let pomodoroMinutes = $state(0);
	let readHnSet = $state(new Set<string>());
	let hnExpanded = $state(false);
	let ytExpanded = $state(false);
	let hnRefreshing = $state(false);
	let ytRefreshing = $state(false);
	let showShutdown = $state(false);
	let showConfetti = $state(false);
	let savedHnIds = $state(new Set<number>());

	let weather = $state<WeatherData | null>(null);
	let weatherLocation = $state('');
	let weatherZip = $state<string | null>(null);
	let showZipInput = $state(false);
	let zipInput = $state('');

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

	function getGreeting(): string {
		const hour = new Date().getHours();
		if (hour < 12) return 'Good morning, Alip';
		if (hour < 17) return 'Good afternoon, Alip';
		return 'Good evening, Alip';
	}

	function timeAgo(isoStr: string): string {
		if (!isoStr) return '';
		const diff = Date.now() - new Date(isoStr).getTime();
		const mins = Math.floor(diff / 60000);
		if (mins < 1) return 'just now';
		if (mins < 60) return `${mins}m ago`;
		const hrs = Math.floor(mins / 60);
		if (hrs < 24) return `${hrs}h ago`;
		return `${Math.floor(hrs / 24)}d ago`;
	}

	function playVideo(videoId: string) {
		activeVideoId = videoId;
		markWatched(videoId);
		watchedSet = new Set([...watchedSet, videoId]);
	}

	function handleDismiss(e: MouseEvent, videoId: string) {
		e.stopPropagation();
		dismissedSet = new Set([...dismissedSet, videoId]);
		dismissVideoServer(videoId);
	}

	function handleHnClick(hnId: number) {
		const id = String(hnId);
		markHnRead(id);
		readHnSet = new Set([...readHnSet, id]);
	}

	async function handleBookmark(e: MouseEvent, post: HnPost) {
		e.preventDefault();
		e.stopPropagation();
		await saveToReadingQueue({ hn_id: post.hn_id, title: post.title, url: post.url || post.hn_url, domain: post.domain });
		savedHnIds = new Set([...savedHnIds, post.hn_id]);
	}

	function syncState(posts: HnPost[], videos: YoutubeVideo[], dismissed: string[]) {
		readHnSet = new Set(posts.filter((p) => isHnRead(String(p.hn_id))).map((p) => String(p.hn_id)));
		watchedSet = new Set(videos.filter((v) => isWatched(v.video_id)).map((v) => v.video_id));
		dismissedSet = new Set(dismissed);
	}

	async function handleHnRefresh() {
		hnRefreshing = true;
		try {
			hnPosts = await refreshHn();
			readHnSet = new Set(hnPosts.filter((p) => isHnRead(String(p.hn_id))).map((p) => String(p.hn_id)));
		} finally {
			hnRefreshing = false;
		}
	}

	async function handleYtRefresh() {
		ytRefreshing = true;
		try {
			ytVideos = await refreshYoutube();
			watchedSet = new Set(ytVideos.filter((v) => isWatched(v.video_id)).map((v) => v.video_id));
		} finally {
			ytRefreshing = false;
		}
	}

	async function setupPushNotifications() {
		if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
		if (Notification.permission !== 'granted') return;
		try {
			const reg = await navigator.serviceWorker.ready;
			const existing = await reg.pushManager.getSubscription();
			if (existing) return; // already subscribed
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

	let confettiShown = false;
	$effect(() => {
		if (pomodoroMinutes >= 240 && !confettiShown) {
			confettiShown = true;
			showConfetti = true;
		}
	});

	$effect(() => {
		setupPushNotifications();
		Promise.all([fetchHnPosts(), fetchYoutubeVideos(), fetchPomodoroToday(), fetchWeather(), fetchDismissedVideoIds()])
			.then(([posts, videos, pomodoro, weatherData, dismissed]) => {
				hnPosts = posts;
				ytVideos = videos;
				syncState(posts, videos, dismissed);
				pomodoroMinutes = pomodoro.total_minutes;
				if (weatherData.weather) {
					weather = weatherData.weather;
					weatherLocation = weatherData.location;
				}
				weatherZip = weatherData.zip_code;
				if (!weatherData.zip_code) showZipInput = true;
			})
			.finally(() => {
				loading = false;
			});
	});

	const visibleVideos = $derived(ytVideos.filter((v) => !dismissedSet.has(v.video_id) && !watchedSet.has(v.video_id)));
	const weatherIcon = $derived(weather ? getWeatherIcon(weather.weather_code) : 'sun');
	const displayedHn = $derived(hnExpanded ? hnPosts : hnPosts.slice(0, 5));
	const displayedYt = $derived(ytExpanded ? visibleVideos : visibleVideos.slice(0, 5));
</script>

<div>
	<div class="page-header">
		<h1 class="greeting">{getGreeting()}</h1>
		<div class="page-header-actions">
			<button class="shutdown-btn" onclick={() => showShutdown = true} aria-label="End of day">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/>
				</svg>
			</button>
			<button class="theme-toggle" onclick={toggleTheme} aria-label="Toggle theme">
				{#if $theme === 'light'}
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
				{:else}
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
				{/if}
			</button>
		</div>
	</div>

	{#if loading && !weather}
		<div class="weather-line">
			<span class="skel skel-inline" style="width: 200px"></span>
		</div>
	{:else if weather}
		<div class="weather-line">
			<span class="weather-icon weather-icon--{weatherIcon}">
				{#if weatherIcon === 'sun'}
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
				{:else if weatherIcon === 'cloud-sun'}
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="M20 12h2"/><path d="m19.07 4.93-1.41 1.41"/><path d="M15.947 12.65a4 4 0 0 0-5.925-4.128"/><path d="M13 22H7a5 5 0 1 1 4.9-6H13a3 3 0 0 1 0 6Z"/></svg>
				{:else if weatherIcon === 'cloud'}
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>
				{:else if weatherIcon === 'rain'}
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M16 14v6"/><path d="M8 14v6"/><path d="M12 16v6"/></svg>
				{:else if weatherIcon === 'snow'}
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M8 15h.01"/><path d="M8 19h.01"/><path d="M12 17h.01"/><path d="M12 21h.01"/><path d="M16 15h.01"/><path d="M16 19h.01"/></svg>
				{:else if weatherIcon === 'storm'}
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 16.326A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 .5 8.973"/><path d="m13 12-3 5h4l-3 5"/></svg>
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
					<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
					{weather.rain_chance}%
				</span>
			{/if}
			<button class="weather-location" onclick={() => showZipInput = !showZipInput}>{weatherLocation}</button>
		</div>
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

	<MitInput />

	<div class="home-top">
		<PomodoroTimer bind:totalMinutesToday={pomodoroMinutes} />
	</div>

	<JournalCard />

	{#if loading}
		<div class="home-section">
			<div class="section-header">
				<span class="skel skel-inline" style="width: 120px; height: 20px"></span>
				<div class="section-actions">
					<span class="skel skel-inline" style="width: 40px; height: 14px"></span>
					<span class="skel" style="width: 30px; height: 30px; border-radius: 6px"></span>
				</div>
			</div>
			{#each Array(5) as _, i}
				<div class="skel-hn-item" class:skel-hn-last={i === 4}>
					<div class="skel skel-line" style="width: {65 + (i % 3) * 10}%"></div>
					<div class="skel skel-line" style="width: 25%; margin-top: 6px; height: 12px"></div>
				</div>
			{/each}
			<div class="skel skel-expand"></div>
		</div>
		<div class="home-section">
			<div class="section-header">
				<span class="skel skel-inline" style="width: 90px; height: 20px"></span>
				<div class="section-actions">
					<span class="skel skel-inline" style="width: 40px; height: 14px"></span>
					<span class="skel" style="width: 30px; height: 30px; border-radius: 6px"></span>
				</div>
			</div>
			{#each Array(5) as _}
				<div class="skel-yt-item">
					<div class="skel skel-yt-thumb"></div>
					<div class="skel-yt-info">
						<div class="skel skel-line" style="width: 85%"></div>
						<div class="skel skel-line" style="width: 45%; margin-top: 8px; height: 12px"></div>
					</div>
				</div>
			{/each}
			<div class="skel skel-expand"></div>
		</div>
	{:else}
		<div class="home-section section-hn">
			<div class="section-header">
				<span class="section-title title-hn">Hacker News</span>
				<div class="section-actions">
					{#if hnPosts.length > 0}
						<span class="section-updated">{timeAgo(hnPosts[0]?.fetched_at)}</span>
					{/if}
					<button class="refresh-btn" onclick={handleHnRefresh} disabled={hnRefreshing}>
						<span class:spinner={hnRefreshing}>↻</span>
					</button>
				</div>
			</div>
			{#if hnPosts.length === 0}
				<div class="empty">No posts yet. Refresh to fetch.</div>
			{:else}
				<ul class="hn-list">
					{#each displayedHn as post, i}
						<li class="hn-item" class:read={readHnSet.has(String(post.hn_id))}>
							<div class="hn-rank-col">
								<span class="hn-rank">{i + 1}</span>
								<button class="hn-bookmark" class:hn-bookmarked={savedHnIds.has(post.hn_id)} onclick={(e) => handleBookmark(e, post)} aria-label="Save to reading queue">
									<svg width="14" height="14" viewBox="0 0 24 24" fill={savedHnIds.has(post.hn_id) ? 'currentColor' : 'none'} stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
								</button>
							</div>
							<div class="hn-content">
								<div class="hn-title">
									<a href={post.url || post.hn_url} target="_blank" rel="noopener" onclick={() => handleHnClick(post.hn_id)}>{post.title}</a>
									{#if post.domain}
										<span class="hn-domain">({post.domain})</span>
									{/if}
								</div>
								<div class="hn-meta">
									<span class="hn-score">{post.score} pts</span>
									<a href={post.hn_url} target="_blank" rel="noopener" onclick={() => handleHnClick(post.hn_id)}>{post.comments} comments</a>
								</div>
							</div>
						</li>
					{/each}
				</ul>
				{#if hnPosts.length > 5}
					<button class="expand-btn" onclick={() => hnExpanded = !hnExpanded}>
						{hnExpanded ? 'Show less' : `Show all ${hnPosts.length}`}
					</button>
				{/if}
			{/if}
		</div>

		<div class="home-section section-yt">
			<div class="section-header">
				<span class="section-title title-yt">YouTube</span>
				<div class="section-actions">
					{#if ytVideos.length > 0}
						<span class="section-updated">{timeAgo(ytVideos[0]?.fetched_at)}</span>
					{/if}
					<button class="refresh-btn" onclick={handleYtRefresh} disabled={ytRefreshing}>
						<span class:spinner={ytRefreshing}>↻</span>
					</button>
				</div>
			</div>
			{#if visibleVideos.length === 0}
				<div class="empty">No videos yet. Add cookies and refresh.</div>
			{:else}
				<div class="yt-grid">
					{#each displayedYt as video}
						<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
						<div
							class="yt-card"
							onclick={() => playVideo(video.video_id)}
						>
							<div class="yt-thumb-container">
								{#if video.thumbnail}
									<img class="yt-thumb" src={video.thumbnail} alt={video.title} loading="lazy" />
								{/if}
								{#if video.duration_label}
									<span class="yt-duration">{video.duration_label}</span>
								{/if}
							</div>
							<div class="yt-info">
								<div class="yt-title">{video.title}</div>
								<div class="yt-channel">{video.channel}</div>
							</div>
							<button
								class="yt-dismiss-icon"
								onclick={(e) => handleDismiss(e, video.video_id)}
								aria-label="Remove video"
							>&times;</button>
						</div>
					{/each}
				</div>
				{#if visibleVideos.length > 5}
					<button class="expand-btn" onclick={() => ytExpanded = !ytExpanded}>
						{ytExpanded ? 'Show less' : `Show all ${visibleVideos.length}`}
					</button>
				{/if}
			{/if}
		</div>
	{/if}

	<ShutdownModal open={showShutdown} onclose={() => showShutdown = false} />
	<Confetti trigger={showConfetti} />
</div>

<VideoPlayer videoId={activeVideoId} onclose={() => (activeVideoId = '')} />
