<script lang="ts">
	import { getToasts, dismissToast } from '$lib/toast.svelte';
	import { X } from 'phosphor-svelte';
</script>

{#if getToasts().length > 0}
	<div class="toast-container">
		{#each getToasts() as toast (toast.id)}
			<div class="toast toast-{toast.type}" role="alert">
				<span class="toast-message">{toast.message}</span>
				<button class="toast-dismiss" onclick={() => dismissToast(toast.id)} aria-label="Dismiss">
					<X size={12} weight="bold" />
				</button>
			</div>
		{/each}
	</div>
{/if}

<style>
	.toast-container {
		position: fixed;
		top: calc(16px + env(safe-area-inset-top, 0px));
		left: 50%;
		transform: translateX(-50%);
		z-index: 9998;
		display: flex;
		flex-direction: column;
		gap: 8px;
		max-width: 400px;
		width: calc(100% - 32px);
		pointer-events: none;
	}

	.toast {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 14px;
		border-radius: var(--radius-md);
		background: var(--card-bg);
		border: 1px solid var(--border);
		box-shadow: var(--shadow-elevated);
		pointer-events: auto;
		animation: toastIn 0.2s ease;
	}

	.toast-error {
		border-color: var(--color-red);
	}

	.toast-success {
		border-color: var(--color-green);
	}

	.toast-message {
		flex: 1;
		font-family: var(--font-sans);
		font-size: 13px;
		color: var(--text);
		line-height: 1.4;
	}

	.toast-dismiss {
		flex-shrink: 0;
		width: 24px;
		height: 24px;
		border: none;
		background: none;
		color: var(--text-tertiary);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0;
		border-radius: var(--radius-sm);
		transition: all 0.15s ease;
	}

	.toast-dismiss:hover {
		background: var(--bg-hover);
		color: var(--text);
	}

	@keyframes toastIn {
		from { opacity: 0; transform: translateY(-8px); }
		to { opacity: 1; transform: translateY(0); }
	}
</style>
