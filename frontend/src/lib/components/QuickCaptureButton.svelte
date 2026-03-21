<script lang="ts">
  import { appendJournalToday } from '$lib/api';
  import { clearCached } from '$lib/cache';
  import { ArrowRight } from 'phosphor-svelte';

  let { open = $bindable(false) }: { open?: boolean } = $props();
  let text = $state('');
  let inputEl: HTMLInputElement;
  let sending = $state(false);

  async function handleSubmit() {
    if (!text.trim() || sending) return;
    sending = true;
    try {
      await appendJournalToday(text.trim());
      clearCached('home');
      window.dispatchEvent(new CustomEvent('journal-updated'));
      text = '';
      open = false;
    } finally {
      sending = false;
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') handleSubmit();
    if (e.key === 'Escape') {
      open = false;
      text = '';
    }
  }

  $effect(() => {
    if (open && inputEl) {
      setTimeout(() => inputEl?.focus(), 50);
    }
  });
</script>

{#if open}
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div
    class="capture-backdrop"
    onclick={() => {
      open = false;
      text = '';
    }}
  ></div>
  <div class="capture-panel">
    <div class="capture-label">Quick Note</div>
    <div class="capture-row">
      <input
        class="capture-input"
        type="text"
        placeholder="Jot something down..."
        bind:value={text}
        bind:this={inputEl}
        onkeydown={handleKeydown}
      />
      <button class="capture-send" onclick={handleSubmit} disabled={!text.trim() || sending}>
        <ArrowRight size={16} weight="duotone" />
      </button>
    </div>
  </div>
{/if}

<style>
  .capture-backdrop {
    position: fixed;
    inset: 0;
    z-index: 98;
    background: rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
  }

  .capture-panel {
    position: fixed;
    bottom: calc(80px + env(safe-area-inset-bottom, 0px));
    left: 20px;
    right: 20px;
    z-index: 99;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px 14px;
    box-shadow:
      0 4px 24px rgba(0, 0, 0, 0.12),
      0 1px 4px rgba(0, 0, 0, 0.06);
    animation: captureSlideUp 0.2s ease;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  :global([data-theme='dark']) .capture-panel {
    box-shadow:
      0 4px 24px rgba(0, 0, 0, 0.4),
      0 1px 4px rgba(0, 0, 0, 0.2);
  }

  .capture-label {
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-tertiary);
  }

  .capture-row {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .capture-input {
    flex: 1;
    padding: 0;
    border: none;
    background: none;
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 14px;
    outline: none;
  }

  .capture-input::placeholder {
    color: var(--text-tertiary);
  }

  .capture-send {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    border: none;
    background: var(--accent);
    color: var(--bg);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: opacity 0.15s;
    -webkit-tap-highlight-color: transparent;
  }

  .capture-send:disabled {
    opacity: 0.3;
  }

  @keyframes captureSlideUp {
    from {
      opacity: 0;
      transform: translateY(8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>
