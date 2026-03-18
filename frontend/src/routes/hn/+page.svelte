<script lang="ts">
	import { fetchHnPosts, refreshHn, type HnPost } from '$lib/api';
	import { isHnRead, markHnRead } from '$lib/watched';

	let posts = $state<HnPost[]>([]);
	let loading = $state(true);
	let refreshing = $state(false);
	let readSet = $state(new Set<string>());

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

	function handleClick(hnId: number) {
		const id = String(hnId);
		markHnRead(id);
		readSet = new Set([...readSet, id]);
	}

	function syncReadState(p: HnPost[]) {
		readSet = new Set(p.filter((post) => isHnRead(String(post.hn_id))).map((post) => String(post.hn_id)));
	}

	async function handleRefresh() {
		refreshing = true;
		try {
			posts = await refreshHn();
			syncReadState(posts);
		} finally {
			refreshing = false;
		}
	}

	$effect(() => {
		fetchHnPosts()
			.then((p) => {
				posts = p;
				syncReadState(p);
			})
			.finally(() => (loading = false));
	});
</script>

<div>
	<div class="section-header">
		<div>
			<span class="section-title">Hacker News</span>
			{#if posts.length > 0}
				<span class="last-updated" style="margin-left: 12px; display: inline;">
					Updated {timeAgo(posts[0]?.fetched_at)}
				</span>
			{/if}
		</div>
		<button class="refresh-btn" onclick={handleRefresh} disabled={refreshing}>
			<span class:spinner={refreshing}>↻</span>
			{refreshing ? 'Refreshing...' : 'Refresh'}
		</button>
	</div>

	{#if loading}
		<div class="loading">Loading posts...</div>
	{:else if posts.length === 0}
		<div class="empty">No posts yet. Hit refresh to fetch from Hacker News.</div>
	{:else}
		<ul class="hn-list">
			{#each posts as post, i}
				<li class="hn-item" class:read={readSet.has(String(post.hn_id))}>
					<span class="hn-rank">{i + 1}</span>
					<div class="hn-content">
						<div class="hn-title">
							<a href={post.url || post.hn_url} target="_blank" rel="noopener" onclick={() => handleClick(post.hn_id)}>{post.title}</a>
							{#if post.domain}
								<span class="hn-domain">({post.domain})</span>
							{/if}
						</div>
						<div class="hn-meta">
							<span class="hn-score">{post.score} pts</span>
							<a href={post.hn_url} target="_blank" rel="noopener" onclick={() => handleClick(post.hn_id)}>{post.comments} comments</a>
						</div>
					</div>
				</li>
			{/each}
		</ul>
	{/if}
</div>
