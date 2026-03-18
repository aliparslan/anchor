<script lang="ts">
	let { videoId = $bindable(''), onclose }: { videoId: string; onclose: () => void } = $props();

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') onclose();
	}

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) onclose();
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if videoId}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div class="player-overlay" onclick={handleBackdropClick}>
		<div class="player-container">
			<button class="player-close" onclick={onclose} aria-label="Close player">&times;</button>
			<div class="player-wrapper">
				<iframe
					src="https://www.youtube-nocookie.com/embed/{videoId}?autoplay=1&rel=0"
					title="Video player"
					frameborder="0"
					allow="autoplay; encrypted-media; picture-in-picture"
					allowfullscreen
				></iframe>
			</div>
		</div>
	</div>
{/if}
