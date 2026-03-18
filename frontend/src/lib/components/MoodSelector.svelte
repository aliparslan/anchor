<script lang="ts">
  let { mood = null, onselect }: { mood: number | null; onselect: (n: number) => void } = $props();

  const faces = ['😩', '😕', '😐', '🙂', '😊'];
  const colors = ['#c75450', '#d4952a', '#c4a06a', '#3a8fc2', '#3d8b6e'];
</script>

<div class="mood-selector">
  <span class="mood-label-text">How's your energy?</span>
  <div class="mood-circles">
    {#each [1, 2, 3, 4, 5] as n, i}
      <button
        class="mood-circle"
        class:mood-selected={mood === n}
        style="--mood-color: {colors[i]}"
        onclick={() => onselect(n)}
        aria-label="Mood {n}"
      >
        <span class="mood-face">{faces[i]}</span>
      </button>
    {/each}
  </div>
</div>

<style>
  .mood-selector {
    margin-bottom: 20px;
  }

  .mood-label-text {
    font-family: var(--font-display);
    font-size: 13px;
    color: var(--text-tertiary);
    display: block;
    margin-bottom: 10px;
  }

  .mood-circles {
    display: flex;
    gap: 12px;
    justify-content: center;
  }

  .mood-circle {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 2px solid var(--border);
    background: var(--bg-inset);
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
  }

  .mood-face {
    font-size: 20px;
    line-height: 1;
    transition: transform 0.2s ease;
  }

  .mood-circle:hover:not(.mood-selected) {
    transform: scale(1.08);
    border-color: var(--text-tertiary);
  }

  .mood-selected {
    border-color: var(--mood-color);
    background: color-mix(in srgb, var(--mood-color) 15%, var(--bg-inset));
    transform: scale(1.12);
    box-shadow: 0 2px 10px color-mix(in srgb, var(--mood-color) 30%, transparent);
  }

  .mood-selected .mood-face {
    transform: scale(1.1);
  }
</style>
