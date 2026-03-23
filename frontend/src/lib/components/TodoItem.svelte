<script lang="ts">
	import type { Todo } from '$lib/api';
	import { tap, success } from '$lib/haptics';
	import { Check, ArrowCounterClockwise, Trash } from 'phosphor-svelte';

	let { todo, oncomplete, onundo, ondelete, onupdate }: {
		todo: Todo;
		oncomplete: (id: number) => void;
		onundo: (id: number) => void;
		ondelete: (id: number) => void;
		onupdate: (id: number, text: string) => void;
	} = $props();

	let editing = $state(false);
	let editText = $state('');
	let editEl: HTMLInputElement;
	let offsetX = $state(0);
	let swiping = $state(false);
	let deleting = $state(false);
	let startX = 0;
	let startY = 0;

	let circleFilled = $state(!!todo.completed_at);

	$effect(() => {
		circleFilled = !!todo.completed_at;
	});

	function startEdit() {
		if (todo.completed_at || circleFilled) return;
		editText = todo.text;
		editing = true;
		requestAnimationFrame(() => editEl?.focus());
	}

	function saveEdit() {
		const trimmed = editText.trim();
		if (trimmed && trimmed !== todo.text) {
			onupdate(todo.id, trimmed);
		}
		editing = false;
	}

	function doComplete() {
		circleFilled = true;
		tap();
		oncomplete(todo.id);
	}

	function doUndo() {
		tap();
		circleFilled = false;
		onundo(todo.id);
	}

	function toggle() {
		if (todo.completed_at || circleFilled) {
			doUndo();
		} else {
			doComplete();
		}
	}

	function handleTouchStart(e: TouchEvent) {
		startX = e.touches[0].clientX;
		startY = e.touches[0].clientY;
		swiping = false;
	}

	function handleTouchMove(e: TouchEvent) {
		const dx = e.touches[0].clientX - startX;
		const dy = e.touches[0].clientY - startY;
		if (!swiping && Math.abs(dx) > 10 && Math.abs(dx) > Math.abs(dy) * 1.5) {
			swiping = true;
			document.body.style.overflow = 'hidden';
		}
		if (swiping) {
			e.preventDefault();
			const absDx = Math.abs(dx);
			const sign = dx > 0 ? 1 : -1;
			offsetX = absDx <= 80 ? dx : sign * (80 + (absDx - 80) * 0.25);
		}
	}

	function handleTouchEnd() {
		document.body.style.overflow = '';
		if (offsetX > 80) {
			if (todo.completed_at || circleFilled) {
				doUndo();
			} else {
				doComplete();
			}
			offsetX = 0;
			swiping = false;
		} else if (offsetX < -80) {
			deleting = true;
			swiping = false;
			offsetX = -(window.innerWidth + 100);
			setTimeout(() => ondelete(todo.id), 300);
		} else {
			offsetX = 0;
			swiping = false;
		}
	}

	const swipeProgress = $derived(Math.min(1, Math.abs(offsetX) / 80));
</script>

<div class="todo-swipe-area"
	class:swipe-right={offsetX > 20}
	class:swipe-left={offsetX < -20}
	style="--swipe-progress: {swipeProgress}">

	{#if offsetX > 30}
		<div class="todo-hint todo-hint-right" style="opacity: {Math.min(1, (offsetX - 30) / 50)}">
			{#if todo.completed_at}
				<ArrowCounterClockwise size={14} weight="bold" />
				<span>Undo</span>
			{:else}
				<Check size={14} weight="bold" />
				<span>Done</span>
			{/if}
		</div>
	{/if}
	{#if offsetX < -30}
		<div class="todo-hint todo-hint-left" style="opacity: {Math.min(1, (-offsetX - 30) / 50)}">
			<Trash size={14} weight="bold" />
			<span>Delete</span>
		</div>
	{/if}

	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div class="todo-row" class:todo-row-done={circleFilled}
		ontouchstart={handleTouchStart}
		ontouchmove={handleTouchMove}
		ontouchend={handleTouchEnd}
		style="transform: translateX({offsetX}px); transition: {swiping ? 'none' : deleting ? 'transform 0.25s ease-in' : 'transform 0.5s cubic-bezier(0.25, 1, 0.5, 1)'}">

		<button class="todo-check"
			class:todo-check-done={circleFilled}
			onclick={toggle}
			aria-label={todo.completed_at ? 'Undo' : 'Complete'}>
			<div class="todo-dot"></div>
		</button>

		{#if editing}
			<input class="todo-input" type="text" bind:value={editText} bind:this={editEl}
				onblur={saveEdit} onkeydown={(e) => e.key === 'Enter' && saveEdit()} />
		{:else}
			<span class="todo-label" class:todo-label-done={circleFilled}
				onclick={startEdit}>
				{todo.text}
			</span>
		{/if}
	</div>
</div>

<style>
	/* === Swipe layer === */
	.todo-swipe-area {
		position: relative;
		overflow: hidden;
	}

	/* Tinted backgrounds during swipe */
	.swipe-right {
		background: rgba(34, 197, 94, calc(0.06 * var(--swipe-progress, 0)));
	}
	.swipe-left {
		background: rgba(239, 68, 68, calc(0.06 * var(--swipe-progress, 0)));
	}

	/* === Row === */
	.todo-row {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 14px 16px;
		background: var(--card-bg);
		-webkit-tap-highlight-color: transparent;
		user-select: none;
		touch-action: pan-y;
		will-change: transform;
		transition: opacity 0.5s ease;
	}

	.todo-row-done {
		opacity: 0.4;
	}

	/* === Circle — ring + inner dot like iOS Reminders === */
	.todo-check {
		width: 20px;
		height: 20px;
		min-width: 20px;
		border-radius: 50%;
		border: 2px solid var(--border);
		background: none;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0;
		transition: border-color 0.15s ease;
		-webkit-tap-highlight-color: transparent;
		position: relative;
		flex-shrink: 0;
	}

	.todo-check:active {
		transform: scale(0.85);
	}

	/* Inner dot — fills from center with gap to ring */
	.todo-dot {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		background: var(--text-secondary);
		transform: scale(0);
		transition: transform 0.15s ease;
		will-change: transform;
	}

	/* Fill animation — slow spring on fill, fast on unfill */
	.todo-check-done {
		border-color: var(--text-secondary);
		transition: border-color 0.5s ease;
	}

	.todo-check-done .todo-dot {
		transform: scale(1);
		transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
	}

	/* === Text === */
	.todo-label {
		flex: 1;
		font-family: var(--font-sans);
		font-size: 14px;
		color: var(--text);
		line-height: 1.4;
		cursor: pointer;
		transition: color 0.5s ease;
	}

	.todo-label-done {
		color: var(--text-tertiary);
		cursor: default;
	}

	/* Edit input — seamless with label */
	.todo-input {
		flex: 1;
		border: none;
		background: none;
		color: var(--text);
		font-family: var(--font-sans);
		font-size: 14px;
		line-height: 1.4;
		outline: none;
		padding: 0;
		margin: 0;
		-webkit-appearance: none;
		appearance: none;
		border-radius: 0;
	}

	/* === Swipe hints === */
	.todo-hint {
		position: absolute;
		top: 0;
		bottom: 0;
		display: flex;
		align-items: center;
		gap: 6px;
		font-family: var(--font-mono);
		font-size: 11px;
		letter-spacing: 0.02em;
		pointer-events: none;
		font-weight: 500;
	}

	.todo-hint-right {
		left: 16px;
		color: var(--color-green);
	}

	.todo-hint-left {
		right: 16px;
		color: #ef4444;
	}
</style>
