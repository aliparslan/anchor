<script lang="ts">
  import { fetchMitToday, saveMit, toggleMit, type Mit } from '$lib/api';
  import { onDestroy } from 'svelte';
  import { tap } from '$lib/haptics';
  import { createAutoSave } from '$lib/autoSave.svelte';

  let mit = $state<Mit | null>(null);
  let text = $state('');
  let completed = $state(false);

  const autoSave = createAutoSave(async () => {
    const saved = await saveMit(text);
    mit = saved;
  });

  function handleInput() {
    autoSave.trigger();
  }

  async function handleToggle() {
    if (!text.trim()) return;
    tap();
    completed = await toggleMit();
  }

  onDestroy(() => {
    autoSave.cleanup();
  });

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
    <div class="mit-dot"></div>
  </button>
  <input
    class="mit-input"
    class:mit-done={completed}
    type="text"
    placeholder="What's the one thing that makes today a win?"
    bind:value={text}
    oninput={handleInput}
  />
  {#if autoSave.saved}
    <span class="mit-saved">Saved</span>
  {/if}
</div>

<style>
  .mit-card {
    display: flex;
    align-items: center;
    gap: 12px;
    border-radius: var(--radius-md);
    padding: var(--space-lg);
    border: 1px solid var(--border);
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
    transition: border-color 0.5s ease;
    -webkit-tap-highlight-color: transparent;
  }

  .mit-check:active {
    transform: scale(0.85);
  }

  .mit-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--accent);
    transform: scale(0);
    transition: transform var(--ease-spring);
    will-change: transform;
  }

  .mit-check-done {
    border-color: var(--accent);
  }

  .mit-check-done .mit-dot {
    transform: scale(1);
  }

  .mit-input {
    flex: 1;
    border: none;
    border-radius: 0;
    background: none;
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 14px;
    outline: none;
    padding: 0;
  }

  .mit-input::placeholder {
    color: var(--text-tertiary);
  }

  .mit-done {
    color: var(--text-tertiary);
    transition: color 0.5s ease;
  }

  .mit-saved {
    font-size: 12px;
    color: var(--text-tertiary);
    font-family: var(--font-mono);
    flex-shrink: 0;
  }
</style>
