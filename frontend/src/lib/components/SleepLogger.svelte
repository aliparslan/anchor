<script lang="ts">
  import { fetchSleepToday, saveSleep, fetchSleepWeek, type SleepDay } from '$lib/api';
  import { formatDuration } from '$lib/format';
  import { onDestroy } from 'svelte';
  import { createAutoSave } from '$lib/autoSave.svelte';

  let bedtime = $state('');
  let wakeTime = $state('');
  let weekData = $state<SleepDay[]>([]);

  function computeDuration(): string {
    if (!bedtime || !wakeTime) return '';
    return formatDuration(durationMinutes(bedtime, wakeTime));
  }

  function durationMinutes(bed: string, wake: string): number {
    const [bh, bm] = bed.split(':').map(Number);
    const [wh, wm] = wake.split(':').map(Number);
    let diff = (wh * 60 + wm) - (bh * 60 + bm);
    if (diff <= 0) diff += 24 * 60;
    return diff;
  }

  const autoSave = createAutoSave(async () => {
    await saveSleep(bedtime, wakeTime);
  }, 800);

  onDestroy(() => {
    autoSave.cleanup();
  });

  function handleChange() {
    if (!bedtime || !wakeTime) return;
    autoSave.trigger();
  }

  $effect(() => {
    fetchSleepToday().then((data) => {
      bedtime = data?.bedtime || '';
      wakeTime = data?.wake_time || '';
    });
    fetchSleepWeek().then((days) => {
      weekData = days;
    });
  });

  const duration = $derived(computeDuration());

  // Sparkline data: hours of sleep per day
  const sparklineHours = $derived(
    weekData.map((d) => {
      if (!d.bedtime || !d.wake_time) return 0;
      return durationMinutes(d.bedtime, d.wake_time) / 60;
    })
  );

  const sparklinePath = $derived.by(() => {
    if (sparklineHours.length < 2) return '';
    const vals = sparklineHours;
    const max = Math.max(...vals, 10);
    const min = Math.min(...vals.filter(v => v > 0), 0);
    const range = max - min || 1;
    const w = 280;
    const h = 48;
    const pad = 4;
    const points = vals.map((v, i) => {
      const x = pad + (i / (vals.length - 1)) * (w - pad * 2);
      const y = h - pad - ((v - min) / range) * (h - pad * 2);
      return `${x},${y}`;
    });
    return points.join(' ');
  });

  const sparklineDots = $derived.by(() => {
    if (sparklineHours.length < 2) return [];
    const vals = sparklineHours;
    const max = Math.max(...vals, 10);
    const min = Math.min(...vals.filter(v => v > 0), 0);
    const range = max - min || 1;
    const w = 280;
    const h = 48;
    const pad = 4;
    return vals.map((v, i) => ({
      x: pad + (i / (vals.length - 1)) * (w - pad * 2),
      y: h - pad - ((v - min) / range) * (h - pad * 2),
      value: v
    }));
  });
</script>

<div class="sleep-logger">
  <div class="sleep-header">
    <span class="sleep-title">Sleep <span class="sleep-range-label">Last 30 days</span></span>
    {#if duration}
      <span class="sleep-duration">{duration}</span>
    {/if}
  </div>
  <div class="sleep-inputs">
    <div class="sleep-field">
      <label class="sleep-label">Bedtime</label>
      <input type="time" class="sleep-time-input" bind:value={bedtime} onchange={handleChange} />
    </div>
    <div class="sleep-field">
      <label class="sleep-label">Wake up</label>
      <input type="time" class="sleep-time-input" bind:value={wakeTime} onchange={handleChange} />
    </div>
  </div>
  {#if sparklineHours.length >= 2}
    <div class="sleep-chart-container">
      <svg class="sleep-chart" viewBox="0 0 280 48">
        <polyline points={sparklinePath} fill="none" stroke="var(--accent)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
        {#each sparklineDots as dot}
          {#if dot.value > 0}
            <circle cx={dot.x} cy={dot.y} r="2.5" fill="var(--accent)" />
          {/if}
        {/each}
      </svg>
      <div class="sleep-chart-labels">
        {#if weekData.length > 0}
          <span class="sleep-chart-day">{new Date(weekData[0].date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
          <span class="sleep-chart-day" style="margin-left: auto">{new Date(weekData[weekData.length - 1].date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
        {/if}
      </div>
    </div>
  {:else if weekData.length > 0}
    <div class="sleep-chart-container">
      <span class="sleep-chart-empty">Graph appears after 2+ days of tracking</span>
    </div>
  {/if}
</div>

<style>
  .sleep-logger {
    border-radius: 10px;
    padding: 16px;
    background: var(--card-bg);
    margin-bottom: var(--space-widget);
  }

  .sleep-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .sleep-title {
    font-family: var(--font-display);
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
  }

  .sleep-duration {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--accent);
    font-weight: 400;
  }

  .sleep-inputs {
    display: flex;
    gap: 16px;
  }

  .sleep-field {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .sleep-label {
    font-size: 11px;
    color: var(--text-tertiary);
    font-family: var(--font-display);
  }

  .sleep-time-input {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
    background: var(--card-bg);
    color: var(--text);
    font-family: var(--font-mono);
    font-size: 14px;
    outline: none;
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    transition: border-color 0.15s ease;
  }

  .sleep-time-input:focus {
    border-color: var(--text-tertiary);
  }

  :global([data-theme='dark']) .sleep-time-input {
    color-scheme: dark;
  }

  .sleep-chart-container {
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px solid var(--border);
  }

  .sleep-chart {
    width: 100%;
    height: 48px;
  }

  .sleep-chart-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 4px;
  }

  .sleep-chart-day {
    font-family: var(--font-mono);
    font-size: 9px;
    color: var(--text-tertiary);
  }

  .sleep-range-label {
    font-weight: 400;
    font-size: 11px;
    color: var(--text-tertiary);
    margin-left: 6px;
  }

  .sleep-chart-empty {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-tertiary);
    text-align: center;
    display: block;
    padding: 8px 0;
  }
</style>
