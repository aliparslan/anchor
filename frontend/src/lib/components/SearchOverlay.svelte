<script lang="ts">
	import { searchAll, type SearchResults } from '$lib/api';
	import { MagnifyingGlass, X } from 'phosphor-svelte';

	let { open = $bindable(false) }: { open: boolean } = $props();
	let query = $state('');
	let results = $state<SearchResults | null>(null);
	let searching = $state(false);
	let searchTimeout: ReturnType<typeof setTimeout> | null = null;
	let inputEl: HTMLInputElement;
	let selectedIndex = $state(-1);

	function handleInput() {
		if (searchTimeout) clearTimeout(searchTimeout);
		selectedIndex = -1;
		if (!query.trim()) {
			results = null;
			searching = false;
			return;
		}
		searching = true;
		searchTimeout = setTimeout(async () => {
			results = await searchAll(query.trim());
			searching = false;
		}, 300);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') { close(); return; }
		if (e.key === 'ArrowDown') { e.preventDefault(); selectedIndex = Math.min(selectedIndex + 1, totalResults - 1); return; }
		if (e.key === 'ArrowUp') { e.preventDefault(); selectedIndex = Math.max(selectedIndex - 1, -1); return; }
		if (e.key === 'Enter' && selectedIndex >= 0) {
			e.preventDefault();
			const el = document.querySelector(`.search-result[data-index="${selectedIndex}"]`) as HTMLElement;
			el?.click();
		}
	}

	function close() {
		open = false;
		query = '';
		results = null;
	}

	$effect(() => {
		if (open && inputEl) {
			setTimeout(() => inputEl?.focus(), 50);
		}
	});

	const totalResults = $derived(
		results ? results.journal.length + results.queue.length + results.rss.length : 0
	);
</script>

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div class="search-overlay" onclick={close}>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div class="search-modal" onclick={(e) => e.stopPropagation()}>
			<div class="search-input-row">
				<MagnifyingGlass size={18} weight="duotone" />
				<input
					class="search-input"
					type="text"
					placeholder="Search everything..."
					bind:value={query}
					bind:this={inputEl}
					oninput={handleInput}
					onkeydown={handleKeydown}
				/>
				{#if searching}
					<span class="search-spinner">...</span>
				{/if}
				<button class="search-close" onclick={close}>
					<X size={16} weight="bold" />
				</button>
			</div>

			{#if results && query.trim()}
				<div class="search-results">
					{#if totalResults === 0}
						<div class="search-empty">No results for "{query}"</div>
					{/if}

					{#if results.journal.length > 0}
						<div class="search-group">
							<span class="search-group-label">Journal</span>
							{#each results.journal.slice(0, 5) as entry}
								<div class="search-result">
									<span class="search-result-meta">{entry.date}</span>
									<span class="search-result-text">{entry.content.slice(0, 100)}</span>
								</div>
							{/each}
						</div>
					{/if}

					{#if results.queue.length > 0}
						<div class="search-group">
							<span class="search-group-label">Saved Articles</span>
							{#each results.queue.slice(0, 5) as item}
								<a href={item.url} target="_blank" rel="noopener" class="search-result search-result-link">
									<span class="search-result-text">{item.title}</span>
									<span class="search-result-meta">{item.domain}</span>
								</a>
							{/each}
						</div>
					{/if}

					{#if results.rss.length > 0}
						<div class="search-group">
							<span class="search-group-label">Articles</span>
							{#each results.rss.slice(0, 5) as item}
								<a href={item.url} target="_blank" rel="noopener" class="search-result search-result-link">
									<span class="search-result-text">{item.title}</span>
									<span class="search-result-meta">{item.feed_name}</span>
								</a>
							{/each}
						</div>
					{/if}
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.search-overlay {
		position: fixed;
		inset: 0;
		z-index: 300;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: flex-start;
		justify-content: center;
		padding: 60px 16px 24px;
		animation: fadeIn 0.15s ease;
	}

	.search-modal {
		background: var(--card-bg);
		border-radius: var(--radius-md);
		width: 100%;
		max-width: 480px;
		max-height: 70vh;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		box-shadow: var(--shadow-elevated);
	}

	.search-input-row {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 14px 16px;
		border-bottom: 1px solid var(--border);
		color: var(--text-tertiary);
	}

	.search-input {
		flex: 1;
		border: none;
		background: none;
		color: var(--text);
		font-family: var(--font-sans);
		font-size: 15px;
		outline: none;
	}

	.search-input::placeholder {
		color: var(--text-tertiary);
	}

	.search-close {
		border: none;
		background: none;
		color: var(--text-tertiary);
		cursor: pointer;
		padding: 4px;
		display: flex;
		border-radius: var(--radius-sm);
		transition: all var(--ease-micro);
	}

	.search-close:hover {
		background: var(--bg-hover);
		color: var(--text);
	}

	.search-results {
		overflow-y: auto;
		padding: 8px;
	}

	.search-empty {
		text-align: center;
		padding: 24px;
		color: var(--text-tertiary);
		font-size: 14px;
	}

	.search-group {
		margin-bottom: 12px;
	}

	.search-group-label {
		display: block;
		font-family: var(--font-display);
		font-size: 10px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--text-tertiary);
		padding: 6px 8px;
	}

	.search-result {
		display: flex;
		flex-direction: column;
		gap: 2px;
		padding: 8px;
		border-radius: var(--radius-sm);
		transition: background 0.1s ease;
		cursor: default;
	}

	.search-result:hover {
		background: var(--bg-hover);
	}

	.search-result-link {
		text-decoration: none;
		cursor: pointer;
	}

	.search-result-text {
		font-size: 13px;
		color: var(--text);
		line-height: 1.4;
	}

	.search-result-meta {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--text-tertiary);
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}
</style>
