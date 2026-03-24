<script lang="ts">
	import {
		fetchHnPosts, fetchYoutubeVideos,
		refreshHn,
		fetchDismissedVideoIds, dismissVideoServer,
		saveToReadingQueue, deleteQueueItemByHnId, deleteQueueItem, fetchReadingQueue,
		markQueueItemRead, markQueueItemUnread,
		fetchRssItems, refreshRss, dismissRssItem, fetchDismissedRssIds,
		type HnPost, type YoutubeVideo, type RssItem, type ReadingQueueItem
	} from '$lib/api';
	import { timeAgo, localDate } from '$lib/utils';
	import { isWatched, markWatched, isHnRead, markHnRead, isRssRead, markRssRead } from '$lib/watched';
	import { getCached, setCached, clearCached } from '$lib/cache';
	import { onDestroy } from 'svelte';
	import VideoPlayer from '$lib/components/VideoPlayer.svelte';
	import { Moon, Sun, ArrowClockwise, BookmarkSimple, X, Check, Eye, EyeSlash } from 'phosphor-svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import SectionHeader from '$lib/components/SectionHeader.svelte';

	// YouTube daily batching: persist reveal count per day in localStorage
	function getYtRevealCount(): number {
		try {
			const today = localDate();
			const storedDate = localStorage.getItem('yt_reveal_date');
			const stored = localStorage.getItem('yt_reveal_count');
			if (storedDate === today && stored) return parseInt(stored, 10);
		} catch {}
		return 10;
	}

	function saveYtRevealCount(count: number) {
		try {
			localStorage.setItem('yt_reveal_count', String(count));
			localStorage.setItem('yt_reveal_date', localDate());
		} catch {}
	}

	// Restore from session cache if available (prevents re-fetch on tab switch)
	const _c = getCached<any>('feed');

	let hnPosts = $state<HnPost[]>(_c?.hnPosts ?? []);
	let ytVideos = $state<YoutubeVideo[]>(_c?.ytVideos ?? []);
	let loading = $state(!_c);
	let fetchError = $state(false);
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
	let readRssUrls = $state<Set<string>>(_c?.readRssUrls ?? new Set());

	// Reading queue
	let queue = $state<ReadingQueueItem[]>(_c?.queue ?? []);
	let queueFilter = $state<'all' | 'unread' | 'read'>('unread');
	let queueExpanded = $state(false);

	function handleRssClick(url: string) {
		markRssRead(url);
		readRssUrls = new Set([...readRssUrls, url]);
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
		if (savedHnIds.has(post.hn_id)) {
			await deleteQueueItemByHnId(post.hn_id);
			const next = new Set(savedHnIds);
			next.delete(post.hn_id);
			savedHnIds = next;
		} else {
			await saveToReadingQueue({ hn_id: post.hn_id, title: post.title, url: post.url || post.hn_url, domain: post.domain });
			savedHnIds = new Set([...savedHnIds, post.hn_id]);
		}
		queue = await fetchReadingQueue();
	}

	function syncState(posts: HnPost[], videos: YoutubeVideo[], dismissed: string[]) {
		readHnSet = new Set(posts.filter((p) => isHnRead(String(p.hn_id))).map((p) => String(p.hn_id)));
		watchedSet = new Set(videos.filter((v) => isWatched(v.video_id)).map((v) => v.video_id));
		dismissedSet = new Set(dismissed);
		readRssUrls = new Set(rssItems.filter((item) => isRssRead(item.url)).map((item) => item.url));
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
			const allQueue = await fetchReadingQueue();
			const queueItem = allQueue.find(q => q.url === item.url);
			if (queueItem) await deleteQueueItem(queueItem.id);
			savedRssUrls = new Set([...savedRssUrls].filter(u => u !== item.url));
		} else {
			const domain = new URL(item.url).hostname.replace('www.', '');
			await saveToReadingQueue({ title: item.title, url: item.url, domain });
			savedRssUrls = new Set([...savedRssUrls, item.url]);
		}
		queue = await fetchReadingQueue();
	}

	function handleRssDismiss(e: MouseEvent, id: number) {
		e.preventDefault();
		e.stopPropagation();
		dismissedRssIds = new Set([...dismissedRssIds, id]);
		dismissRssItem(id);
	}

	async function handleRssRefresh() {
		rssRefreshing = true;
		try {
			rssItems = await refreshRss();
			readRssUrls = new Set(rssItems.filter((item) => isRssRead(item.url)).map((item) => item.url));
		} finally {
			rssRefreshing = false;
		}
	}

	function getDomain(url: string): string {
		try { return new URL(url).hostname.replace('www.', ''); } catch { return ''; }
	}

	async function handleQueueClick(item: ReadingQueueItem) {
		markQueueItemRead(item.id);
		window.open(item.url, '_blank');
		queue = queue.map((q) => q.id === item.id ? { ...q, read_at: new Date().toISOString() } : q);
	}

	async function handleToggleRead(e: MouseEvent, item: ReadingQueueItem) {
		e.stopPropagation();
		e.preventDefault();
		if (item.read_at) {
			await markQueueItemUnread(item.id);
			queue = queue.map((q) => q.id === item.id ? { ...q, read_at: null } : q);
		} else {
			await markQueueItemRead(item.id);
			queue = queue.map((q) => q.id === item.id ? { ...q, read_at: new Date().toISOString() } : q);
		}
	}

	async function handleQueueDelete(e: MouseEvent, id: number) {
		e.stopPropagation();
		e.preventDefault();
		await deleteQueueItem(id);
		queue = queue.filter((q) => q.id !== id);
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
			fetchRssItems(),
			fetchDismissedRssIds()
		])
			.then(([posts, videos, dismissed, queueItems, rss, dismissedRss]) => {
				hnPosts = posts;
				ytVideos = videos;
				rssItems = rss;
				queue = queueItems;
				dismissedRssIds = new Set(dismissedRss);
				syncState(posts, videos, dismissed);
				savedHnIds = new Set(
					queueItems
						.filter((q: any) => q.hn_id != null)
						.map((q: any) => q.hn_id as number)
				);
			})
			.catch((err) => { console.warn('[Feed] fetch error:', err); fetchError = true; })
			.finally(() => {
				loading = false;
			});
	});

	// Save state to session cache on destroy (persists across tab switches)
	onDestroy(() => {
		setCached('feed', {
			hnPosts, ytVideos, readHnSet, watchedSet, dismissedSet,
			savedHnIds, ytRevealCount, rssItems, savedRssUrls,
			dismissedRssIds: [...dismissedRssIds], readRssUrls, queue
		});
	});

	const visibleVideos = $derived(
		ytVideos
			.filter((v) => !dismissedSet.has(v.video_id))
			.slice(0, ytRevealCount)
	);
	const canRevealMoreYt = $derived(ytRevealCount < ytVideos.length);
	const displayedHn = $derived(hnExpanded ? hnPosts.slice(0, 10) : hnPosts.slice(0, 5));
	const filteredRss = $derived(rssItems.filter(item => !dismissedRssIds.has(item.id)));
	const displayedRss = $derived(rssExpanded ? filteredRss.slice(0, 20) : filteredRss.slice(0, 10));
	const filteredQueue = $derived(
		queueFilter === 'all' ? queue
		: queueFilter === 'unread' ? queue.filter((q) => !q.read_at)
		: queue.filter((q) => q.read_at)
	);
	const unreadCount = $derived(queue.filter((q) => !q.read_at).length);
	const readCount = $derived(queue.filter((q) => q.read_at).length);
</script>

<div>
	{#if fetchError}
		<p class="fetch-error">Couldn't load feed</p>
	{/if}
	<PageHeader title="Feed" />

	{#if loading}
		<!-- Skeleton: HN -->
		<div>
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
		<div style="margin-top: var(--space-section)">
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
		<div class="section-hn">
			<SectionHeader title="Hacker News">
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
			</SectionHeader>
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
		<div class="section-yt" style="margin-top: var(--space-section)">
			<SectionHeader title="YouTube">
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
			</SectionHeader>
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
							class:watched={watchedSet.has(video.video_id)}
							style="animation-delay: {vi * 40}ms"
							onclick={() => playVideo(video.video_id)}
						>
							<div class="yt-thumb-container">
								{#if video.thumbnail}
									<img class="yt-thumb" src={video.thumbnail} alt={video.title} loading="lazy" width="160" height="90" />
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
		<div style="margin-top: var(--space-section)">
			<SectionHeader title="Articles">
				<div class="section-actions">
					<button class="refresh-btn" onclick={handleRssRefresh} disabled={rssRefreshing}>
						<span class:spinner={rssRefreshing}>
							<ArrowClockwise size={14} weight="bold" />
						</span>
					</button>
				</div>
			</SectionHeader>
			{#if rssItems.length === 0}
				<div class="empty">No articles yet. Feeds update every 12 hours.</div>
			{:else}
				<ul class="hn-list">
					{#each displayedRss as item}
						<li class="hn-item" class:read={readRssUrls.has(item.url)}>
							<button class="hn-bookmark" class:hn-bookmarked={savedRssUrls.has(item.url)} onclick={(e) => handleRssBookmark(e, item)} aria-label="Save to reading queue">
								<BookmarkSimple size={14} weight={savedRssUrls.has(item.url) ? "fill" : "regular"} />
							</button>
							<div class="hn-content">
								<div class="hn-title">
									<a href={item.url} target="_blank" rel="noopener" onclick={() => handleRssClick(item.url)}>{item.title}</a>
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
		<!-- Reading Queue -->
		{#if queue.length > 0}
			<div style="margin-top: var(--space-section)">
				<SectionHeader title="Queue">
					<div class="section-actions">
						<div class="queue-filters">
							<button class="queue-filter" class:queue-filter-active={queueFilter === 'unread'} onclick={() => queueFilter = 'unread'}>
								Unread {unreadCount}
							</button>
							<button class="queue-filter" class:queue-filter-active={queueFilter === 'read'} onclick={() => queueFilter = 'read'}>
								Read {readCount}
							</button>
							<button class="queue-filter" class:queue-filter-active={queueFilter === 'all'} onclick={() => queueFilter = 'all'}>
								All
							</button>
						</div>
					</div>
				</SectionHeader>
				{#if filteredQueue.length === 0}
					<div class="empty">{queueFilter === 'unread' ? 'All caught up' : 'No read articles yet'}</div>
				{:else}
					<ul class="hn-list">
						{#each filteredQueue as item}
							<li class="hn-item" class:read={item.read_at !== null}>
								<div class="hn-content">
									<div class="hn-title">
										<a href={item.url} target="_blank" rel="noopener" onclick={() => handleQueueClick(item)}>
											{item.title}
											{#if item.domain}
												<span class="hn-domain">({item.domain})</span>
											{:else}
												<span class="hn-domain">({getDomain(item.url)})</span>
											{/if}
										</a>
									</div>
									<div class="hn-meta">
										<span>saved {timeAgo(item.saved_at)}</span>
									</div>
								</div>
								<div class="queue-actions">
									<button class="queue-action-btn" onclick={(e) => handleToggleRead(e, item)} aria-label={item.read_at ? 'Mark unread' : 'Mark read'}>
										{#if item.read_at}
											<EyeSlash size={14} weight="duotone" />
										{:else}
											<Eye size={14} weight="duotone" />
										{/if}
									</button>
									<button class="queue-action-btn" onclick={(e) => handleQueueDelete(e, item.id)} aria-label="Remove">
										<X size={14} weight="bold" />
									</button>
								</div>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		{/if}
	{/if}
</div>

<VideoPlayer videoId={activeVideoId} onclose={() => (activeVideoId = '')} />

<style>
/* HN Post list */
.hn-list {
	list-style: none;
	border-radius: var(--radius-md);
	background: var(--card-bg);
	border: 1px solid var(--border);
	padding: 4px 14px;
	margin-bottom: var(--space-widget);
}

.hn-item {
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 10px 0;
	border-bottom: 1px solid var(--border);
	transition: opacity 0.15s ease;
}

.hn-item:last-child {
	border-bottom: none;
}

.hn-rank {
	font-size: 14px;
	color: var(--text-tertiary);
	min-width: 20px;
	text-align: center;
	font-variant-numeric: tabular-nums;
	line-height: 1.4;
	padding-top: 1px;
}

.hn-content {
	flex: 1;
	min-width: 0;
}

.hn-title {
	font-size: 15px;
	line-height: 1.4;
	font-weight: 400;
}

.hn-title a:hover {
	color: var(--accent);
}

.hn-domain {
	font-size: 12px;
	color: var(--text-tertiary);
	margin-left: 6px;
}

.hn-meta {
	display: flex;
	gap: 12px;
	margin-top: 4px;
	font-family: var(--font-mono);
	font-size: 11px;
	color: var(--text-secondary);
}

.hn-meta a:hover {
	color: var(--accent);
}

.hn-score {
	display: inline-flex;
	align-items: center;
	gap: 3px;
}

/* HN read state */
.hn-item.read {
	opacity: 0.45;
}

.hn-item.read:hover {
	opacity: 0.7;
}

.hn-rank-col {
	display: flex;
	flex-direction: column;
	align-items: center;
	min-width: 20px;
	padding-top: 0;
	gap: 4px;
}

/* HN Bookmark */
.hn-bookmark {
	flex-shrink: 0;
	background: none;
	border: none;
	color: var(--text-tertiary);
	cursor: pointer;
	padding: 4px;
	transition: all 0.15s ease;
}

.hn-bookmark:not(.hn-bookmarked) {
	opacity: 0.5;
}

.hn-bookmark:hover {
	color: var(--accent);
}

.hn-bookmarked {
	color: var(--accent);
	opacity: 1;
}

/* YouTube list */
.yt-grid {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.yt-card {
	display: flex;
	align-items: center;
	gap: 14px;
	border-radius: var(--radius-md);
	overflow: hidden;
	background: var(--card-bg);
	border: 1px solid var(--border);
	transition: box-shadow 0.15s ease, transform 0.15s ease;
	cursor: pointer;
	padding: 8px;
	width: 100%;
	text-align: left;
	font-family: inherit;
	font-size: inherit;
	color: inherit;
}

.yt-card:hover {
	box-shadow: var(--shadow-hover);
}

.yt-card:active {
	transform: scale(0.98);
}

.yt-thumb-container {
	position: relative;
	width: 160px;
	min-width: 160px;
	aspect-ratio: 16 / 9;
	overflow: hidden;
	background: var(--bg-secondary);
	border-radius: var(--radius-sm);
}

.yt-thumb {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.yt-duration {
	position: absolute;
	bottom: 4px;
	right: 4px;
	padding: 1px 5px;
	border-radius: var(--radius-sm);
	background: rgba(0, 0, 0, 0.8);
	color: #fff;
	font-family: var(--font-mono);
	font-size: 10px;
	font-weight: 400;
}

.yt-info {
	flex: 1;
	min-width: 0;
	padding: 2px 0;
}

.yt-title {
	font-size: 14px;
	font-weight: 500;
	line-height: 1.4;
	display: -webkit-box;
	-webkit-line-clamp: 3;
	-webkit-box-orient: vertical;
	overflow: hidden;
}

.yt-channel {
	font-size: 12px;
	color: var(--text-secondary);
	margin-top: 4px;
}

/* Watched state */
.yt-card.watched {
	opacity: 0.45;
}

.yt-card.watched:hover {
	opacity: 0.7;
}

/* Dismiss button: X icon on far right, visible on hover */
.yt-dismiss-icon {
	flex-shrink: 0;
	width: 28px;
	height: 28px;
	border-radius: var(--radius-sm);
	border: none;
	background: none;
	color: var(--text-tertiary);
	cursor: pointer;
	display: flex;
	align-items: center;
	justify-content: center;
	opacity: 0;
	transition: all 0.15s ease;
	font-family: inherit;
	padding: 0;
}

.yt-card:hover .yt-dismiss-icon {
	opacity: 1;
}

.yt-dismiss-icon:hover {
	background: var(--bg-hover);
	color: var(--text);
}

/* Queue filters & actions */
.queue-filters {
	display: flex;
	gap: 4px;
}

.queue-filter {
	padding: 3px 8px;
	border-radius: var(--radius-md);
	border: none;
	background: var(--bg-secondary);
	color: var(--text-tertiary);
	font-family: var(--font-mono);
	font-size: 10px;
	font-weight: 500;
	cursor: pointer;
	transition: all 0.15s ease;
}

.queue-filter-active {
	background: var(--text);
	color: var(--bg);
}

.queue-actions {
	display: flex;
	gap: 2px;
	flex-shrink: 0;
}

.queue-action-btn {
	width: 28px;
	height: 28px;
	border-radius: var(--radius-sm);
	border: none;
	background: none;
	color: var(--text-tertiary);
	cursor: pointer;
	display: flex;
	align-items: center;
	justify-content: center;
	transition: all 0.15s ease;
	padding: 0;
	-webkit-tap-highlight-color: transparent;
}

.queue-action-btn:hover {
	background: var(--bg-hover);
	color: var(--text);
}

/* Refresh button */
.refresh-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 36px;
	height: 36px;
	border-radius: var(--radius-sm);
	border: 1px solid var(--border);
	background: var(--bg);
	color: var(--text-secondary);
	cursor: pointer;
	font-size: 14px;
	font-family: inherit;
	transition: all var(--ease-micro);
}

.refresh-btn:hover {
	background: var(--bg-hover);
	color: var(--text);
	border-color: var(--text-tertiary);
}

.refresh-btn:disabled {
	opacity: 0.5;
	cursor: not-allowed;
}

.refresh-btn span {
	display: flex;
	align-items: center;
	justify-content: center;
}

.refresh-btn .spinner {
	animation: spin 1s linear infinite;
}

@keyframes spin {
	from { transform: rotate(0deg); }
	to { transform: rotate(360deg); }
}

.section-updated {
	font-family: var(--font-mono);
	font-size: 11px;
	color: var(--text-tertiary);
	white-space: nowrap;
}

.section-actions {
	display: flex;
	align-items: center;
	gap: var(--space-sm);
}

/* Skeleton items */
.skel-hn-item {
	padding: 10px 14px;
	padding-left: 46px;
	border-bottom: 1px solid var(--border);
}

.skel-hn-item.skel-hn-last {
	border-bottom: none;
}

.skel-yt-item {
	display: flex;
	align-items: center;
	gap: 14px;
	padding: var(--space-sm);
	border: 1px solid var(--border);
	border-radius: var(--radius-md);
	margin-bottom: var(--space-sm);
}

.skel-yt-item:last-child {
	margin-bottom: 0;
}

.skel-yt-thumb {
	width: 160px;
	min-width: 160px;
	aspect-ratio: 16 / 9;
	border-radius: var(--radius-sm);
}

.skel-yt-info {
	flex: 1;
	min-width: 0;
	padding: 2px 0;
}

.skel-expand {
	height: 38px;
	margin-top: var(--space-sm);
	border-radius: var(--radius-sm);
}

/* Responsive */
@media (max-width: 600px) {
	.yt-thumb-container {
		width: 120px;
		min-width: 120px;
	}

	.yt-dismiss-icon {
		opacity: 1;
	}

	.skel-yt-thumb {
		width: 120px;
		min-width: 120px;
	}
}
</style>
