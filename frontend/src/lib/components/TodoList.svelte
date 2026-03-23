<script lang="ts">
	import { fetchTodos, createTodo, completeTodo, undoTodo, deleteTodo, updateTodo, type Todo } from '$lib/api';
	import TodoItem from './TodoItem.svelte';
	import { flip } from 'svelte/animate';

	let todos = $state<Todo[]>([]);
	let loaded = $state(false);
	let newText = $state('');
	let inputEl: HTMLInputElement;
	let inputFocused = $state(false);

	const sorted = $derived(
		[...todos].sort((a, b) => {
			if (!a.completed_at && !b.completed_at) return a.position - b.position;
			if (a.completed_at && !b.completed_at) return 1;
			if (!a.completed_at && b.completed_at) return -1;
			return 0;
		})
	);

	$effect(() => {
		fetchTodos().then(t => { todos = t; loaded = true; });
	});

	async function addTodo() {
		if (!newText.trim()) return;
		const todo = await createTodo(newText.trim());
		todos = [...todos, todo];
		newText = '';
	}

	function handleInputKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addTodo();
		}
	}

	async function handleComplete(id: number) {
		const updated = await completeTodo(id);
		todos = todos.map(t => t.id === id ? updated : t);
	}

	async function handleUndo(id: number) {
		const updated = await undoTodo(id);
		todos = todos.map(t => t.id === id ? updated : t);
	}

	async function handleDelete(id: number) {
		await deleteTodo(id);
		todos = todos.filter(t => t.id !== id);
	}

	async function handleUpdate(id: number, text: string) {
		const updated = await updateTodo(id, text);
		todos = todos.map(t => t.id === id ? updated : t);
	}
</script>

{#if loaded}
	<div class="todo-list">
		{#each sorted as todo, i (todo.id)}
			<div class="todo-entrance" style="animation-delay: {i * 40}ms"
				animate:flip={{ duration: 500, easing: (t) => 1 - Math.pow(1 - t, 3) }}>
				<TodoItem {todo} oncomplete={handleComplete} onundo={handleUndo} ondelete={handleDelete} onupdate={handleUpdate} />
			</div>
		{/each}

		<div class="todo-add-row" class:todo-add-focused={inputFocused}>
			<div class="todo-add-circle" class:todo-add-circle-active={inputFocused}></div>
			<input class="todo-add-input" type="text"
				bind:value={newText} bind:this={inputEl}
				placeholder="Add a task..."
				onkeydown={handleInputKeydown}
				onfocus={() => inputFocused = true}
				onblur={() => inputFocused = false} />
		</div>
	</div>
{/if}

<style>
	.todo-list {
		border-radius: 10px;
		background: var(--card-bg);
		border: 1px solid var(--border);
		overflow: hidden;
	}

	/* Staggered entrance — only opacity, no transform (avoids flip conflict) */
	.todo-entrance {
		animation: todoFadeIn 0.3s ease both;
	}

	@keyframes todoFadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}

	/* Add row */
	.todo-add-row {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 14px 16px;
		transition: background 0.2s ease;
	}

	.todo-add-focused {
		background: var(--bg-hover);
	}

	.todo-add-circle {
		width: 20px;
		height: 20px;
		min-width: 20px;
		border-radius: 50%;
		border: 2px dashed var(--border);
		transition: border-color 0.2s ease;
	}

	.todo-add-circle-active {
		border-color: var(--text-tertiary);
	}

	.todo-add-input {
		flex: 1;
		border: none;
		background: none;
		color: var(--text);
		font-family: var(--font-sans);
		font-size: 14px;
		outline: none;
		padding: 0;
	}

	.todo-add-input::placeholder {
		color: var(--text-tertiary);
	}
</style>
