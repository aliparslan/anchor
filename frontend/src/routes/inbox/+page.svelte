<script lang="ts">
	import {
		fetchReadingQueue, markQueueItemRead, markQueueItemUnread, deleteQueueItem,
		fetchCaptures, archiveCapture, deleteCapture,
		type ReadingQueueItem, type Capture
	} from '$lib/api';
	import { timeAgo } from '$lib/utils';
	import { theme, toggleTheme } from '$lib/theme';
	import { getCached, setCached, clearCached } from '$lib/cache';
	import { onDestroy } from 'svelte';
	import { Check, X, Moon, Sun, Eye, EyeSlash } from 'phosphor-svelte';

	const _c = getCached<any>('inbox');

	let queue = $state<ReadingQueueItem[]>(_c?.queue ?? []);
	let captures = $state<Capture[]>(_c?.captures ?? []);
	let filter = $state<'all' | 'unread' | 'read'>('unread');

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
		clearCached('home');
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
		if (_c) return;
		Promise.all([fetchReadingQueue(), fetchCaptures()]).then(([q, c]) => {
			queue = q;
			captures = c;
		});
	});

	onDestroy(() => {
		setCached('inbox', { queue, captures });
	});

	const filteredQueue = $derived(
		filter === 'all' ? queue
		: filter === 'unread' ? queue.filter((q) => !q.read_at)
		: queue.filter((q) => q.read_at)
	);

	const unreadCount = $derived(queue.filter((q) => !q.read_at).length);
	const readCount = $derived(queue.filter((q) => q.read_at).length);
</script>

<div class="page-header">
	<h1 class="greeting">Inbox</h1>
	<button class="theme-toggle" onclick={toggleTheme} aria-label="Toggle theme">
		{#if $theme === 'light'}
			<Moon size={18} weight="duotone" />
		{:else}
			<Sun size={18} weight="duotone" />
		{/if}
	</button>
</div>

<!-- Reading Queue -->
<div class="home-section">
	<div class="section-header">
		<span class="section-title">Reading Queue</span>
	</div>

	{#if queue.length > 0}
		<div class="filter-pills">
			<button class="filter-pill" class:filter-active={filter === 'unread'} onclick={() => filter = 'unread'}>
				Unread{#if unreadCount > 0} <span class="filter-count">{unreadCount}</span>{/if}
			</button>
			<button class="filter-pill" class:filter-active={filter === 'read'} onclick={() => filter = 'read'}>
				Read{#if readCount > 0} <span class="filter-count">{readCount}</span>{/if}
			</button>
			<button class="filter-pill" class:filter-active={filter === 'all'} onclick={() => filter = 'all'}>
				All
			</button>
		</div>
	{/if}

	{#if queue.length === 0}
		<div class="empty">No saved articles<br><span class="empty-hint">Bookmark articles from the Feed tab</span></div>
	{:else if filteredQueue.length === 0}
		<div class="empty">{filter === 'unread' ? 'All caught up' : 'No read articles yet'}</div>
	{:else}
		<div class="inbox-list">
			{#each filteredQueue as item}
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
					<div class="inbox-item-actions">
						<button class="inbox-action-btn inbox-action-eye" onclick={(e) => handleToggleRead(e, item)} aria-label={item.read_at ? 'Mark unread' : 'Mark read'}>
							{#if item.read_at}
								<EyeSlash size={16} weight="duotone" />
							{:else}
								<Eye size={16} weight="duotone" />
							{/if}
						</button>
						<button class="inbox-action-btn inbox-action-delete" onclick={(e) => handleQueueDelete(e, item.id)} aria-label="Remove">
							<X size={16} weight="bold" />
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Captured Notes -->
<div class="home-section">
	<div class="section-header">
		<span class="section-title">Notes</span>
	</div>
	{#if captures.length === 0}
		<div class="empty">No captured notes<br><span class="empty-hint">Tap the + button to capture a thought</span></div>
	{:else}
		<div class="inbox-list">
			{#each captures as capture}
				<div class="inbox-item">
					<div class="inbox-item-content">
						<span class="inbox-capture-text">{capture.text}</span>
						<span class="inbox-item-time">{timeAgo(capture.created_at)}</span>
					</div>
					<div class="inbox-item-actions">
						<button class="inbox-action-btn" onclick={() => handleArchiveCapture(capture.id)} aria-label="Archive">
							<Check size={16} weight="bold" />
						</button>
						<button class="inbox-action-btn inbox-action-delete" onclick={() => handleDeleteCapture(capture.id)} aria-label="Delete">
							<X size={16} weight="bold" />
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.filter-pills {
		display: flex;
		gap: 6px;
		margin-bottom: 14px;
	}

	.filter-pill {
		padding: 5px 12px;
		border-radius: 20px;
		border: none;
		background: var(--bg-secondary);
		color: var(--text-tertiary);
		font-family: var(--font-display);
		font-size: 12px;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.15s ease;
		display: flex;
		align-items: center;
		gap: 5px;
	}

	.filter-pill:hover {
		border-color: var(--text-tertiary);
		color: var(--text-secondary);
	}

	.filter-active {
		background: var(--accent);
		border-color: var(--accent);
		color: white;
	}

	.filter-active:hover {
		background: var(--accent-hover);
		border-color: var(--accent-hover);
		color: white;
	}

	.filter-count {
		font-family: var(--font-mono);
		font-size: 11px;
	}

	.inbox-list {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.inbox-item {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 14px 16px;
		border-radius: 8px;
		background: var(--card-bg);
		transition: box-shadow 0.15s ease;
	}

	.inbox-item:hover {
		box-shadow: var(--shadow-hover);
	}

	.inbox-item-read {
		opacity: 0.5;
	}

	.inbox-item-read:hover {
		opacity: 0.7;
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

	.inbox-item-actions {
		display: flex;
		gap: 4px;
		flex-shrink: 0;
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
		color: var(--accent);
	}

	.inbox-action-delete:hover {
		color: var(--text);
	}

	.inbox-action-eye {
		color: var(--text-tertiary);
	}

	@media (max-width: 600px) {
		.inbox-item-actions {
			opacity: 1;
		}
	}
</style>
