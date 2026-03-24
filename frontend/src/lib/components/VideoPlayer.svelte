<script lang="ts">
	import { X } from 'phosphor-svelte';

	let { videoId = $bindable(''), onclose }: { videoId: string; onclose: () => void } = $props();

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') onclose();
	}

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) onclose();
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if videoId}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div class="player-overlay" onclick={handleBackdropClick}>
		<div class="player-container">
			<button class="player-close" onclick={onclose} aria-label="Close player">
				<X size={24} weight="bold" color="#fff" />
			</button>
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

<style>
/* Video player overlay */
.player-overlay {
	position: fixed;
	inset: 0;
	z-index: 100;
	background: rgba(0, 0, 0, 0.75);
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 24px;
}

.player-container {
	position: relative;
	width: 100%;
	max-width: 900px;
}

.player-close {
	position: absolute;
	top: -40px;
	right: 0;
	background: none;
	border: none;
	color: #fff;
	cursor: pointer;
	opacity: 0.7;
	transition: opacity 0.15s ease;
	line-height: 1;
	display: flex;
	align-items: center;
}

.player-close:hover {
	opacity: 1;
}

.player-wrapper {
	position: relative;
	width: 100%;
	padding-bottom: 56.25%; /* 16:9 */
	background: #000;
	border-radius: var(--radius-md);
	overflow: hidden;
}

.player-wrapper iframe {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
}
</style>
