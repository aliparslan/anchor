<script lang="ts">
  import { fetchMitToday, saveMit, toggleMit, type Mit } from '$lib/api';

  let mit = $state<Mit | null>(null);
  let text = $state('');
  let completed = $state(false);
  let saveTimeout: ReturnType<typeof setTimeout> | null = null;

  async function handleInput() {
    if (saveTimeout) clearTimeout(saveTimeout);
    saveTimeout = setTimeout(async () => {
      const saved = await saveMit(text);
      mit = saved;
    }, 1500);
  }

  async function handleToggle() {
    if (!text.trim()) return;
    completed = await toggleMit();
  }

  $effect(() => {
    fetchMitToday().then((data) => {
      mit = data;
      text = data?.text || '';
      completed = !!data?.completed;
    });
  });
</script>

<div class="mit-card">
  <button class="mit-check" class:mit-check-done={completed} onclick={handleToggle} aria-label="Toggle MIT complete" disabled={!text.trim()}>
    {#if completed}
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
    {/if}
  </button>
  <input
    class="mit-input"
    class:mit-done={completed}
    type="text"
    placeholder="What's the one thing that makes today a win?"
    bind:value={text}
    oninput={handleInput}
  />
</div>

<style>
  .mit-card {
    display: flex;
    align-items: center;
    gap: 12px;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 16px;
    background: var(--card-bg);
    margin-bottom: var(--space-widget);
  }

  .mit-check {
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
    transition: all 0.2s ease;
    color: var(--text-tertiary);
  }

  .mit-check:active {
    transform: scale(1.15);
  }

  .mit-check-done {
    background: var(--color-habits);
    border-color: var(--color-habits);
    color: white;
  }

  .mit-input {
    flex: 1;
    border: none;
    background: none;
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 14px;
    outline: none;
  }

  .mit-input::placeholder {
    color: var(--text-tertiary);
  }

  .mit-done {
    text-decoration: line-through;
    color: var(--text-tertiary);
    transition: color 0.2s ease, text-decoration 0.2s ease;
  }
</style>
