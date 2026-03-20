<script lang="ts">
  import { fetchMitToday, saveMit, toggleMit, type Mit } from '$lib/api';
  import { onDestroy } from 'svelte';
  import { Check } from 'phosphor-svelte';
  import { tap } from '$lib/haptics';

  let mit = $state<Mit | null>(null);
  let text = $state('');
  let completed = $state(false);
  let saveTimeout: ReturnType<typeof setTimeout> | null = null;
  let savedIndicator = $state(false);
  let indicatorTimeout: ReturnType<typeof setTimeout> | null = null;

  async function handleInput() {
    if (saveTimeout) clearTimeout(saveTimeout);
    saveTimeout = setTimeout(async () => {
      const saved = await saveMit(text);
      mit = saved;
      savedIndicator = true;
      if (indicatorTimeout) clearTimeout(indicatorTimeout);
      indicatorTimeout = setTimeout(() => { savedIndicator = false; }, 2000);
    }, 1500);
  }

  async function handleToggle() {
    if (!text.trim()) return;
    tap();
    completed = await toggleMit();
  }

  onDestroy(() => {
    if (saveTimeout) clearTimeout(saveTimeout);
    if (indicatorTimeout) clearTimeout(indicatorTimeout);
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
    {#if completed}
      <Check size={12} weight="bold" />
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
  {#if savedIndicator}
    <span class="mit-saved">Saved</span>
  {/if}
</div>

<style>
  .mit-card {
    display: flex;
    align-items: center;
    gap: 12px;
    border-radius: 10px;
    padding: 12px 16px;
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
    transition: all 0.2s ease;
    color: var(--text-tertiary);
  }

  .mit-check:active {
    transform: scale(1.15);
  }

  .mit-check-done {
    background: var(--accent);
    border-color: var(--accent);
    color: var(--bg);
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

  .mit-saved {
    font-size: 12px;
    color: var(--text-tertiary);
    font-family: var(--font-mono);
    flex-shrink: 0;
  }

  .mit-done {
    text-decoration: line-through;
    color: var(--text-tertiary);
    transition: color 0.2s ease, text-decoration 0.2s ease;
  }
</style>
