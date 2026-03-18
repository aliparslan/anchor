<script lang="ts">
  import { SmileyXEyes, SmileySad, SmileyMeh, Smiley, SmileyWink } from 'phosphor-svelte';

  let { mood = null, onselect }: { mood: number | null; onselect: (n: number) => void } = $props();

  const faces = [SmileyXEyes, SmileySad, SmileyMeh, Smiley, SmileyWink];
  const moodColors = ['#e04545', '#e68a3a', '#c4a06a', '#3b82f6', '#22c55e'];
</script>

<div class="mood-selector">
  <span class="mood-label-text">How's your mood?</span>
  <div class="mood-circles">
    {#each [1, 2, 3, 4, 5] as n, i}
      {@const Face = faces[i]}
      <button
        class="mood-circle"
        class:mood-selected={mood === n}
        style="--mood-color: {moodColors[i]}"
        onclick={() => onselect(n)}
        aria-label="Mood {n}"
      >
        <Face size={28} weight="duotone" />
      </button>
    {/each}
  </div>
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
    border-radius: 50%;
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
</style>
