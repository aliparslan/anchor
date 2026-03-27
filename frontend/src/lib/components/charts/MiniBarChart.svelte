<script lang="ts">
  interface BarDatum {
    label: string;
    value: number;
    highlighted?: boolean;
  }

  let {
    data = [],
    max = 0,
    height = 96,
    color = 'var(--accent)',
    goalLine,
    formatValue,
  }: {
    data: BarDatum[];
    max?: number;
    height?: number;
    color?: string;
    goalLine?: number;
    formatValue?: (v: number) => string;
  } = $props();

  const effectiveMax = $derived(max || Math.max(...data.map((d) => d.value), 1));
  const goalPercent = $derived(goalLine ? Math.min(100, (goalLine / effectiveMax) * 100) : null);
</script>

<div class="mini-bar-chart" style="height: {height}px; --bar-color: {color}">
  <div class="bar-area">
    {#if goalPercent !== null}
      <div class="goal-line" style="bottom: {goalPercent}%"></div>
    {/if}
    {#each data as d}
      {@const pct = Math.min(100, (d.value / effectiveMax) * 100)}
      <div class="bar-col" class:bar-col-highlighted={d.highlighted}>
        {#if formatValue && d.value > 0}
          <span class="bar-value">{formatValue(d.value)}</span>
        {/if}
        <div class="bar-track">
          <div class="bar-fill" style="height: {pct}%"></div>
        </div>
        <span class="bar-label" class:bar-label-highlighted={d.highlighted}>{d.label}</span>
      </div>
    {/each}
  </div>
</div>

<style>
  .mini-bar-chart {
    width: 100%;
    position: relative;
  }

  .bar-area {
    display: flex;
    align-items: flex-end;
    gap: 6px;
    height: 100%;
    position: relative;
    padding-bottom: 20px;
  }

  .bar-col {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    height: 100%;
    justify-content: flex-end;
    position: relative;
  }

  .bar-value {
    font-family: var(--font-mono);
    font-size: 9px;
    color: var(--text-tertiary);
    opacity: 0;
    transition: opacity 0.15s ease;
    position: absolute;
    top: -2px;
    white-space: nowrap;
  }

  .bar-col:hover .bar-value {
    opacity: 1;
  }

  .bar-track {
    width: 100%;
    max-width: 28px;
    flex: 1;
    display: flex;
    align-items: flex-end;
    border-radius: var(--radius-sm);
    background: color-mix(in srgb, var(--bar-color) 10%, transparent);
    overflow: hidden;
  }

  .bar-fill {
    width: 100%;
    border-radius: var(--radius-sm);
    background: var(--bar-color);
    min-height: 3px;
    transition: height 0.4s cubic-bezier(0.25, 1, 0.5, 1);
  }

  .bar-label {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-tertiary);
    flex-shrink: 0;
    position: absolute;
    bottom: 0;
  }

  .bar-label-highlighted {
    color: var(--text);
    font-weight: 600;
  }

  .goal-line {
    position: absolute;
    left: 0;
    right: 0;
    border-top: 1.5px dashed color-mix(in srgb, var(--bar-color) 40%, transparent);
    z-index: 1;
    pointer-events: none;
  }
</style>
