<script lang="ts">
  import { fetchFocusMonth, type FocusDay } from '$lib/api';

  let data = $state<FocusDay[]>([]);

  $effect(() => {
    fetchFocusMonth().then((d) => (data = d));
  });

  const grid = $derived.by(() => {
    const today = new Date();
    const lookup = new Map(data.map((d) => [d.date, d.minutes]));
    const days: { date: string; minutes: number }[] = [];

    for (let i = 29; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const iso = d.toISOString().split('T')[0];
      days.push({ date: iso, minutes: lookup.get(iso) || 0 });
    }
    return days;
  });

  function intensity(minutes: number): string {
    if (minutes === 0) return 'heatmap-empty';
    if (minutes < 120) return 'heatmap-low';
    if (minutes < 180) return 'heatmap-mid';
    return 'heatmap-high';
  }

  function label(d: { date: string; minutes: number }): string {
    const hrs = Math.round(d.minutes / 60 * 10) / 10;
    return `${d.date}: ${hrs}h`;
  }
</script>

<div class="heatmap-card">
  <div class="heatmap-header">
    <span class="heatmap-title">Focus</span>
    <span class="heatmap-subtitle">Last 30 days</span>
  </div>
  <div class="heatmap-grid">
    {#each grid as day}
      <div class="heatmap-cell {intensity(day.minutes)}" title={label(day)}></div>
    {/each}
  </div>
  <div class="heatmap-legend">
    <span class="heatmap-legend-label">Less</span>
    <div class="heatmap-cell heatmap-empty heatmap-legend-cell"></div>
    <div class="heatmap-cell heatmap-low heatmap-legend-cell"></div>
    <div class="heatmap-cell heatmap-mid heatmap-legend-cell"></div>
    <div class="heatmap-cell heatmap-high heatmap-legend-cell"></div>
    <span class="heatmap-legend-label">More</span>
  </div>
</div>

<style>
  .heatmap-card {
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    background: var(--card-bg);
    margin-bottom: var(--space-widget);
  }

  .heatmap-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .heatmap-title {
    font-family: var(--font-display);
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
  }

  .heatmap-subtitle {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-tertiary);
  }

  .heatmap-grid {
    display: grid;
    grid-template-columns: repeat(10, 1fr);
    grid-template-rows: repeat(3, 1fr);
    gap: 3px;
    grid-auto-flow: column;
  }

  .heatmap-cell {
    aspect-ratio: 1;
    border-radius: 3px;
    background: var(--bg-inset);
    transition: background 0.15s ease;
  }

  .heatmap-empty {
    background: var(--bg-inset);
  }

  .heatmap-low {
    background: color-mix(in srgb, var(--accent) 30%, var(--bg-inset));
  }

  .heatmap-mid {
    background: color-mix(in srgb, var(--accent) 60%, var(--bg-inset));
  }

  .heatmap-high {
    background: var(--accent);
  }

  .heatmap-legend {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 3px;
    margin-top: 8px;
  }

  .heatmap-legend-label {
    font-family: var(--font-mono);
    font-size: 9px;
    color: var(--text-tertiary);
    margin: 0 2px;
  }

  .heatmap-legend-cell {
    width: 10px;
    height: 10px;
    aspect-ratio: auto;
  }
</style>
