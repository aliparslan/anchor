<script lang="ts">
  import { page } from '$app/state';
  import { saveCapture } from '$lib/api';

  let isOpen = $state(false);
  let text = $state('');
  let inputEl: HTMLInputElement;

  async function handleSubmit() {
    if (!text.trim()) return;
    await saveCapture(text.trim());
    text = '';
    isOpen = false;
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') handleSubmit();
    if (e.key === 'Escape') {
      isOpen = false;
      text = '';
    }
  }

  $effect(() => {
    if (isOpen && inputEl) {
      // Small delay for mobile keyboard to appear before focusing
      setTimeout(() => inputEl?.focus(), 50);
    }
  });

  const hidden = $derived(page.url.pathname === '/inbox');
</script>

{#if !hidden}
  {#if isOpen}
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div
      class="capture-backdrop"
      onclick={() => {
        isOpen = false;
        text = '';
      }}
    ></div>
    <div class="capture-panel">
      <input
        class="capture-input"
        type="text"
        placeholder="Capture a thought..."
        bind:value={text}
        bind:this={inputEl}
        onkeydown={handleKeydown}
      />
      <button class="capture-send" onclick={handleSubmit} disabled={!text.trim()}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
    </div>
  {/if}
  <button class="capture-fab" class:capture-fab-open={isOpen} onclick={() => (isOpen = !isOpen)} aria-label="Quick capture">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  </button>
{/if}

<style>
  .capture-fab {
    position: fixed;
    bottom: calc(74px + env(safe-area-inset-bottom, 0px));
    right: 20px;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: none;
    background: var(--accent);
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
    z-index: 99;
    transition: all 0.2s ease;
  }

  .capture-fab:hover {
    transform: scale(1.08);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  }

  .capture-fab-open {
    transform: rotate(45deg);
  }

  .capture-fab-open:hover {
    transform: rotate(45deg) scale(1.08);
  }

  .capture-backdrop {
    position: fixed;
    inset: 0;
    z-index: 98;
    background: rgba(0, 0, 0, 0.15);
  }

  .capture-panel {
    position: fixed;
    bottom: calc(130px + env(safe-area-inset-bottom, 0px));
    right: 20px;
    display: flex;
    gap: 8px;
    z-index: 99;
    animation: captureSlideUp 0.2s ease;
  }

  .capture-input {
    width: 260px;
    padding: 10px 14px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--card-bg);
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 14px;
    outline: none;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
  }

  .capture-input:focus {
    border-color: var(--accent);
  }

  .capture-send {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    border: none;
    background: var(--accent);
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: opacity 0.15s;
  }

  .capture-send:disabled {
    opacity: 0.4;
  }

  @keyframes captureSlideUp {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>
