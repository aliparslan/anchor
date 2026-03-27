<script lang="ts">
  import { SmileyXEyes, SmileySad, SmileyMeh, Smiley, SmileyWink } from 'phosphor-svelte';
  import { tap } from '$lib/haptics';

  let { mood = null, onselect }: { mood: number | null; onselect: (n: number) => void } = $props();

  let expanded = $state(false);

  const faces = [SmileyXEyes, SmileySad, SmileyMeh, Smiley, SmileyWink];
  const moodLabels = ['Awful', 'Low', 'Okay', 'Good', 'Great'];
  const moodColors = ['#e04545', '#e68a3a', '#c4a06a', '#3b82f6', '#22c55e'];

  function handleSelect(n: number) {
    tap();
    onselect(n);
    expanded = false;
  }

  const showExpanded = $derived(expanded || mood === null);
</script>

<div class="mood-selector">
  {#if showExpanded}
    <span class="mood-label-text">How's your mood?</span>
    <div class="mood-circles">
      {#each [1, 2, 3, 4, 5] as n, i}
        {@const Face = faces[i]}
        <button
          class="mood-circle"
          class:mood-selected={mood === n}
          style="--mood-color: {moodColors[i]}"
          onclick={() => handleSelect(n)}
          aria-label="Mood {n}"
        >
          <Face size={28} weight="duotone" />
        </button>
      {/each}
    </div>
  {:else if mood !== null}
    {@const Face = faces[mood - 1]}
    <button class="mood-compact" onclick={() => expanded = true} style="--mood-color: {moodColors[mood - 1]}">
      <span class="mood-compact-icon" style="color: {moodColors[mood - 1]}">
        <Face size={20} weight="duotone" />
      </span>
      <span class="mood-compact-label">{moodLabels[mood - 1]}</span>
      <span class="mood-compact-change">Change</span>
    </button>
  {/if}
</div>

<style>
  .mood-selector {
    margin-bottom: var(--space-widget);
  }

  .mood-label-text {
    font-family: var(--font-display);
    font-size: 13px;
    color: var(--text-tertiary);
    display: block;
    margin-bottom: 8px;
  }

  .mood-circles {
    display: flex;
    gap: 0;
    justify-content: space-between;
    padding: 0 8px;
  }

  .mood-circle {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-full);
    border: 2px solid var(--border);
    background: var(--bg-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    color: var(--text-tertiary);
  }

  .mood-circle:hover:not(.mood-selected) {
    transform: scale(1.08);
    border-color: var(--mood-color);
    color: var(--mood-color);
  }

  .mood-circle:active {
    transform: scale(0.92);
  }

  .mood-selected {
    border-color: var(--mood-color);
    background: var(--card-bg);
    color: var(--mood-color);
    transform: scale(1.12);
    box-shadow: 0 0 0 2px color-mix(in srgb, var(--mood-color) 25%, transparent);
  }

  .mood-compact {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 12px 16px;
    border-radius: var(--radius-md);
    border: 1px solid var(--border);
    background: var(--card-bg);
    cursor: pointer;
    transition: background var(--ease-micro);
  }

  .mood-compact:hover {
    background: var(--bg-hover);
  }

  .mood-compact:active {
    transform: scale(0.98);
  }

  .mood-compact-icon {
    display: flex;
    align-items: center;
  }

  .mood-compact-label {
    font-family: var(--font-display);
    font-size: 15px;
    font-weight: 500;
    color: var(--text);
    flex: 1;
    text-align: left;
  }

  .mood-compact-change {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-tertiary);
  }
</style>
