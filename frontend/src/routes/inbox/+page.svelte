<script lang="ts">
	import {
		fetchReadingQueue, markQueueItemRead, deleteQueueItem,
		fetchCaptures, archiveCapture, deleteCapture,
		type ReadingQueueItem, type Capture
	} from '$lib/api';
	import { theme, toggleTheme } from '$lib/theme';

	let queue = $state<ReadingQueueItem[]>([]);
	let captures = $state<Capture[]>([]);

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

	function getDomain(url: string): string {
		try {
			return new URL(url).hostname.replace('www.', '');
		} catch {
			return '';
		}
	}

	async function handleQueueClick(item: ReadingQueueItem) {
		markQueueItemRead(item.id);
		window.open(item.url, '_blank');
		queue = queue.map((q) => q.id === item.id ? { ...q, read_at: new Date().toISOString() } : q);
	}

	async function handleQueueDelete(e: MouseEvent, id: number) {
		e.stopPropagation();
		e.preventDefault();
		await deleteQueueItem(id);
		queue = queue.filter((q) => q.id !== id);
	}

	async function handleArchiveCapture(id: number) {
		await archiveCapture(id);
		captures = captures.filter((c) => c.id !== id);
	}

	async function handleDeleteCapture(id: number) {
		await deleteCapture(id);
		captures = captures.filter((c) => c.id !== id);
	}

	$effect(() => {
		Promise.all([fetchReadingQueue(), fetchCaptures()]).then(([q, c]) => {
			queue = q;
			captures = c;
		});
	});
</script>

<div class="page-header">
	<h1 class="greeting">Inbox</h1>
	<button class="theme-toggle" onclick={toggleTheme} aria-label="Toggle theme">
		{#if $theme === 'light'}
			<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
		{:else}
			<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
		{/if}
	</button>
</div>

<!-- Reading Queue -->
<div class="home-section">
	<div class="section-header">
		<span class="section-title title-inbox">Reading Queue</span>
	</div>
	{#if queue.length === 0}
		<div class="empty">No saved articles</div>
	{:else}
		<div class="inbox-list">
			{#each queue as item}
				<div class="inbox-item" class:inbox-item-read={item.read_at !== null}>
					<div class="inbox-item-content">
						<a href={item.url} target="_blank" rel="noopener" class="inbox-item-title" onclick={() => handleQueueClick(item)}>
							{item.title}
							{#if item.domain}
								<span class="inbox-item-domain">({item.domain})</span>
							{:else}
								<span class="inbox-item-domain">({getDomain(item.url)})</span>
							{/if}
						</a>
						<span class="inbox-item-time">saved {timeAgo(item.saved_at)}</span>
					</div>
					<button class="inbox-item-remove" onclick={(e) => handleQueueDelete(e, item.id)} aria-label="Remove">
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
					</button>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Captured Notes -->
<div class="home-section">
	<div class="section-header">
		<span class="section-title title-inbox">Notes</span>
	</div>
	{#if captures.length === 0}
		<div class="empty">No captured notes</div>
	{:else}
		<div class="inbox-list">
			{#each captures as capture}
				<div class="inbox-item">
					<div class="inbox-item-content">
						<span class="inbox-capture-text">{capture.text}</span>
						<span class="inbox-item-time">{timeAgo(capture.created_at)}</span>
					</div>
					<div class="inbox-item-actions">
						<button class="inbox-action-btn inbox-action-archive" onclick={() => handleArchiveCapture(capture.id)} aria-label="Archive">
							<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
						</button>
						<button class="inbox-action-btn inbox-action-delete" onclick={() => handleDeleteCapture(capture.id)} aria-label="Delete">
							<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.inbox-list {
		border: 1px solid var(--border);
		border-radius: 10px;
		overflow: hidden;
	}

	.inbox-item {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 14px 16px;
		border-bottom: 1px solid var(--border);
		transition: background 0.1s ease;
	}

	.inbox-item:last-child {
		border-bottom: none;
	}

	.inbox-item:hover {
		background: var(--bg-hover);
	}

	.inbox-item-read {
		opacity: 0.5;
	}

	.inbox-item-content {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.inbox-item-title {
		font-size: 14px;
		font-weight: 400;
		line-height: 1.4;
		color: var(--text);
		text-decoration: none;
	}

	.inbox-item-title:hover {
		color: var(--accent);
	}

	.inbox-item-domain {
		font-size: 12px;
		color: var(--text-tertiary);
		margin-left: 4px;
	}

	.inbox-item-time {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--text-tertiary);
	}

	.inbox-capture-text {
		font-size: 14px;
		line-height: 1.5;
		color: var(--text);
	}

	.inbox-item-remove {
		flex-shrink: 0;
		width: 28px;
		height: 28px;
		border-radius: 6px;
		border: none;
		background: none;
		color: var(--text-tertiary);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		opacity: 0;
		transition: all 0.15s ease;
		padding: 0;
	}

	.inbox-item:hover .inbox-item-remove {
		opacity: 1;
	}

	.inbox-item-remove:hover {
		background: var(--bg-hover);
		color: var(--text);
	}

	.inbox-item-actions {
		display: flex;
		gap: 4px;
		flex-shrink: 0;
		opacity: 0;
		transition: opacity 0.15s ease;
	}

	.inbox-item:hover .inbox-item-actions {
		opacity: 1;
	}

	.inbox-action-btn {
		width: 28px;
		height: 28px;
		border-radius: 6px;
		border: none;
		background: none;
		color: var(--text-tertiary);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.15s ease;
		padding: 0;
	}

	.inbox-action-btn:hover {
		background: var(--bg-hover);
		color: var(--color-habits);
	}

	.inbox-action-delete:hover {
		color: var(--color-yt);
	}

	@media (max-width: 600px) {
		.inbox-item-remove,
		.inbox-item-actions {
			opacity: 1;
		}
	}
</style>
