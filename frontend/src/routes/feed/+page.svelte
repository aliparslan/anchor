<script lang="ts">
	import {
		fetchHnPosts, fetchYoutubeVideos,
		refreshHn,
		fetchDismissedVideoIds, dismissVideoServer,
		saveToReadingQueue, deleteQueueItemByHnId, deleteQueueItem, fetchReadingQueue,
		fetchRssItems, refreshRss,
		type HnPost, type YoutubeVideo, type RssItem
	} from '$lib/api';
	import { timeAgo } from '$lib/utils';
	import { isWatched, markWatched, isHnRead, markHnRead } from '$lib/watched';
	import { theme, toggleTheme } from '$lib/theme';
	import { getCached, setCached, clearCached } from '$lib/cache';
	import { onDestroy } from 'svelte';
	import VideoPlayer from '$lib/components/VideoPlayer.svelte';
	import { Moon, Sun, ArrowClockwise, BookmarkSimple, X, Check } from 'phosphor-svelte';

	// YouTube daily batching: persist reveal count per day in localStorage
	function getYtRevealCount(): number {
		try {
			const today = new Date().toISOString().split('T')[0];
			const storedDate = localStorage.getItem('yt_reveal_date');
			const stored = localStorage.getItem('yt_reveal_count');
			if (storedDate === today && stored) return parseInt(stored, 10);
		} catch {}
		return 10;
	}

	function saveYtRevealCount(count: number) {
		try {
			localStorage.setItem('yt_reveal_count', String(count));
			localStorage.setItem('yt_reveal_date', new Date().toISOString().split('T')[0]);
		} catch {}
	}

	// Restore from session cache if available (prevents re-fetch on tab switch)
	const _c = getCached<any>('feed');

	let hnPosts = $state<HnPost[]>(_c?.hnPosts ?? []);
	let ytVideos = $state<YoutubeVideo[]>(_c?.ytVideos ?? []);
	let loading = $state(!_c);
	let activeVideoId = $state('');
	let watchedSet = $state<Set<string>>(_c?.watchedSet ?? new Set());
	let dismissedSet = $state<Set<string>>(_c?.dismissedSet ?? new Set());
	let readHnSet = $state<Set<string>>(_c?.readHnSet ?? new Set());
	let hnExpanded = $state(false);
	let ytRevealCount = $state(_c?.ytRevealCount ?? getYtRevealCount());
	let hnRefreshing = $state(false);
	let savedHnIds = $state<Set<number>>(_c?.savedHnIds ?? new Set());
	let rssItems = $state<RssItem[]>(_c?.rssItems ?? []);
	let rssExpanded = $state(false);
	let rssRefreshing = $state(false);
	let savedRssUrls = $state<Set<string>>(_c?.savedRssUrls ?? new Set());
	let dismissedRssIds = $state<Set<number>>(new Set(_c?.dismissedRssIds ? [..._c.dismissedRssIds] : []));

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
		if (savedHnIds.has(post.hn_id)) {
			await deleteQueueItemByHnId(post.hn_id);
			const next = new Set(savedHnIds);
			next.delete(post.hn_id);
			savedHnIds = next;
		} else {
			await saveToReadingQueue({ hn_id: post.hn_id, title: post.title, url: post.url || post.hn_url, domain: post.domain });
			savedHnIds = new Set([...savedHnIds, post.hn_id]);
		}
		// Invalidate inbox cache so it re-fetches with updated queue
		clearCached('inbox');
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

	async function handleRssBookmark(e: MouseEvent, item: RssItem) {
		e.preventDefault();
		e.stopPropagation();
		if (savedRssUrls.has(item.url)) {
			const queue = await fetchReadingQueue();
			const queueItem = queue.find(q => q.url === item.url);
			if (queueItem) await deleteQueueItem(queueItem.id);
			savedRssUrls = new Set([...savedRssUrls].filter(u => u !== item.url));
			clearCached('inbox');
		} else {
			const domain = new URL(item.url).hostname.replace('www.', '');
			await saveToReadingQueue({ title: item.title, url: item.url, domain });
			savedRssUrls = new Set([...savedRssUrls, item.url]);
			clearCached('inbox');
		}
	}

	function handleRssDismiss(e: MouseEvent, id: number) {
		e.preventDefault();
		e.stopPropagation();
		dismissedRssIds = new Set([...dismissedRssIds, id]);
	}

	async function handleRssRefresh() {
		rssRefreshing = true;
		try {
			rssItems = await refreshRss();
		} finally {
			rssRefreshing = false;
		}
	}

	function handleYtRevealMore() {
		if (ytRevealCount < ytVideos.length) {
			ytRevealCount = Math.min(ytRevealCount + 10, ytVideos.length);
			saveYtRevealCount(ytRevealCount);
		}
	}

	// Fetch data (skipped if restored from session cache)
	$effect(() => {
		if (_c) return;
		Promise.all([
			fetchHnPosts(),
			fetchYoutubeVideos(),
			fetchDismissedVideoIds(),
			fetchReadingQueue(),
			fetchRssItems()
		])
			.then(([posts, videos, dismissed, queueItems, rss]) => {
				hnPosts = posts;
				ytVideos = videos;
				rssItems = rss;
				syncState(posts, videos, dismissed);
				// Populate saved HN IDs from reading queue
				savedHnIds = new Set(
					queueItems
						.filter((q: any) => q.hn_id != null)
						.map((q: any) => q.hn_id as number)
				);
			})
			.finally(() => {
				loading = false;
			});
	});

	// Save state to session cache on destroy (persists across tab switches)
	onDestroy(() => {
		setCached('feed', {
			hnPosts, ytVideos, readHnSet, watchedSet, dismissedSet,
			savedHnIds, ytRevealCount, rssItems, savedRssUrls,
			dismissedRssIds: [...dismissedRssIds]
		});
	});

	const visibleVideos = $derived(
		ytVideos
			.filter((v) => !dismissedSet.has(v.video_id) && !watchedSet.has(v.video_id))
			.slice(0, ytRevealCount)
	);
	const canRevealMoreYt = $derived(ytRevealCount < ytVideos.length);
	const displayedHn = $derived(hnExpanded ? hnPosts.slice(0, 10) : hnPosts.slice(0, 5));
	const filteredRss = $derived(rssItems.filter(item => !dismissedRssIds.has(item.id)));
	const displayedRss = $derived(rssExpanded ? filteredRss.slice(0, 20) : filteredRss.slice(0, 10));
</script>

<div>
	<div class="page-header">
		<h1 class="greeting">Feed</h1>
		<button class="theme-toggle" onclick={toggleTheme} aria-label="Toggle theme">
			{#if $theme === 'light'}
				<Moon size={18} weight="duotone" />
			{:else}
				<Sun size={18} weight="duotone" />
			{/if}
		</button>
	</div>

	{#if loading}
		<!-- Skeleton: HN -->
		<div class="home-section">
			<div class="section-header">
				<span class="skel skel-inline" style="width: 120px; height: 14px"></span>
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
		<!-- Skeleton: YouTube -->
		<div class="home-section">
			<div class="section-header">
				<span class="skel skel-inline" style="width: 90px; height: 14px"></span>
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
		</div>
	{:else}
		<!-- Hacker News -->
		<div class="home-section section-hn">
			<div class="section-header">
				<span class="section-title">Hacker News</span>
				<div class="section-actions">
					{#if hnPosts.length > 0}
						<span class="section-updated">{timeAgo(hnPosts[0]?.fetched_at)}</span>
					{/if}
					<button class="refresh-btn" onclick={handleHnRefresh} disabled={hnRefreshing}>
						<span class:spinner={hnRefreshing}>
							<ArrowClockwise size={14} weight="bold" />
						</span>
					</button>
				</div>
			</div>
			{#if hnPosts.length === 0}
				<div class="empty">No posts yet. Refresh to fetch.</div>
			{:else}
				<ul class="hn-list">
					{#each displayedHn as post, i}
						<li class="hn-item stagger-in" style="animation-delay: {i * 40}ms" class:read={readHnSet.has(String(post.hn_id))}>
							<div class="hn-rank-col">
								<span class="hn-rank">{i + 1}</span>
								<button class="hn-bookmark" class:hn-bookmarked={savedHnIds.has(post.hn_id)} onclick={(e) => handleBookmark(e, post)} aria-label={savedHnIds.has(post.hn_id) ? 'Remove bookmark' : 'Save to reading queue'}>
									<BookmarkSimple size={14} weight={savedHnIds.has(post.hn_id) ? 'fill' : 'regular'} />
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
						{hnExpanded ? 'Show less' : `Show all ${Math.min(10, hnPosts.length)}`}
					</button>
				{/if}
			{/if}
		</div>

		<!-- YouTube (daily batching) -->
		<div class="home-section section-yt">
			<div class="section-header">
				<span class="section-title">YouTube</span>
				<div class="section-actions">
					{#if ytVideos.length > 0}
						<span class="section-updated">{timeAgo(ytVideos[0]?.fetched_at)}</span>
					{/if}
					{#if canRevealMoreYt}
						<button class="refresh-btn" onclick={handleYtRevealMore}>
							<ArrowClockwise size={14} weight="bold" />
						</button>
					{:else}
						<button class="refresh-btn" disabled>
							<Check size={14} weight="bold" />
						</button>
					{/if}
				</div>
			</div>
			{#if visibleVideos.length === 0 && !canRevealMoreYt}
				<div class="empty">All caught up for today.</div>
			{:else if visibleVideos.length === 0}
				<div class="empty">No videos yet. Add cookies and refresh.</div>
			{:else}
				<div class="yt-grid">
					{#each visibleVideos as video, vi}
						<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
						<div
							class="yt-card stagger-in"
							style="animation-delay: {vi * 40}ms"
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
							><X size={16} weight="bold" /></button>
						</div>
					{/each}
				</div>
				{#if canRevealMoreYt}
					<button class="expand-btn" onclick={handleYtRevealMore}>
						Show more ({Math.min(10, ytVideos.length - ytRevealCount)} remaining)
					</button>
				{/if}
			{/if}
		</div>

		<!-- Articles (RSS) -->
		<div class="home-section">
			<div class="section-header">
				<span class="section-title">Articles</span>
				<div class="section-actions">
					<button class="refresh-btn" onclick={handleRssRefresh} disabled={rssRefreshing}>
						<span class:spinner={rssRefreshing}>
							<ArrowClockwise size={14} weight="bold" />
						</span>
					</button>
				</div>
			</div>
			{#if rssItems.length === 0}
				<div class="empty">No articles yet. Feeds update every 12 hours.</div>
			{:else}
				<ul class="hn-list">
					{#each displayedRss as item}
						<li class="hn-item">
							<button class="hn-bookmark" class:hn-bookmarked={savedRssUrls.has(item.url)} onclick={(e) => handleRssBookmark(e, item)} aria-label="Save to reading queue">
								<BookmarkSimple size={14} weight={savedRssUrls.has(item.url) ? "fill" : "regular"} />
							</button>
							<div class="hn-content">
								<div class="hn-title">
									<a href={item.url} target="_blank" rel="noopener">{item.title}</a>
									<span class="hn-domain">({item.feed_name})</span>
								</div>
								<div class="hn-meta">
									<span>{item.author}</span>
									{#if item.published_at}
										<span>{timeAgo(item.published_at)}</span>
									{/if}
								</div>
							</div>
							<button class="yt-dismiss-icon" onclick={(e) => handleRssDismiss(e, item.id)} aria-label="Dismiss">
								<X size={14} weight="bold" />
							</button>
						</li>
					{/each}
				</ul>
				{#if filteredRss.length > 10}
					<button class="expand-btn" onclick={() => rssExpanded = !rssExpanded}>
						{rssExpanded ? 'Show less' : `Show more (${Math.min(10, filteredRss.length - 10)} more)`}
					</button>
				{/if}
			{/if}
		</div>
	{/if}
</div>

<VideoPlayer videoId={activeVideoId} onclose={() => (activeVideoId = '')} />
