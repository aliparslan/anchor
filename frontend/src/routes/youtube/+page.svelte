<script lang="ts">
	import { fetchYoutubeVideos, refreshYoutube, fetchDismissedVideoIds, dismissVideoServer, type YoutubeVideo } from '$lib/api';
	import { isWatched, markWatched } from '$lib/watched';
	import VideoPlayer from '$lib/components/VideoPlayer.svelte';

	let videos = $state<YoutubeVideo[]>([]);
	let loading = $state(true);
	let refreshing = $state(false);
	let activeVideoId = $state('');
	let watchedSet = $state(new Set<string>());
	let dismissedSet = $state(new Set<string>());

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

	async function handleRefresh() {
		refreshing = true;
		try {
			videos = await refreshYoutube();
			watchedSet = new Set(videos.filter((v) => isWatched(v.video_id)).map((v) => v.video_id));
		} finally {
			refreshing = false;
		}
	}

	$effect(() => {
		Promise.all([fetchYoutubeVideos(), fetchDismissedVideoIds()])
			.then(([v, dismissed]) => {
				videos = v;
				watchedSet = new Set(v.filter((vid) => isWatched(vid.video_id)).map((vid) => vid.video_id));
				dismissedSet = new Set(dismissed);
			})
			.finally(() => (loading = false));
	});

	const visibleVideos = $derived(videos.filter((v) => !dismissedSet.has(v.video_id)));
</script>

<div>
	<div class="section-header">
		<div>
			<span class="section-title">YouTube</span>
			{#if videos.length > 0}
				<span class="last-updated" style="margin-left: 12px; display: inline;">
					Updated {timeAgo(videos[0]?.fetched_at)}
				</span>
			{/if}
		</div>
		<button class="refresh-btn" onclick={handleRefresh} disabled={refreshing}>
			<span class:spinner={refreshing}>↻</span>
			{refreshing ? 'Refreshing...' : 'Refresh'}
		</button>
	</div>

	{#if loading}
		<div class="loading">Loading videos...</div>
	{:else if visibleVideos.length === 0}
		<div class="empty">No videos yet. Make sure cookies.txt is in the data/ folder and hit refresh.</div>
	{:else}
		<div class="yt-grid">
			{#each visibleVideos as video}
				<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
				<div
					class="yt-card"
					class:watched={watchedSet.has(video.video_id)}
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
	{/if}
</div>

<VideoPlayer videoId={activeVideoId} onclose={() => (activeVideoId = '')} />
