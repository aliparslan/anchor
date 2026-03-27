<script lang="ts">
  import { fetchSleepToday, saveSleep, fetchSleepWeek, type SleepDay } from '$lib/api';
  import { formatDuration } from '$lib/format';
  import { onDestroy } from 'svelte';
  import { createAutoSave } from '$lib/autoSave.svelte';
  import MiniLineChart from './charts/MiniLineChart.svelte';

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

  function formatDateLabel(dateStr: string): string {
    return new Date(dateStr + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  const chartData = $derived(
    weekData.map((d) => ({
      label: formatDateLabel(d.date),
      value: d.bedtime && d.wake_time ? durationMinutes(d.bedtime, d.wake_time) / 60 : 0,
    }))
  );
</script>

<div class="sleep-logger">
  <div class="sleep-header">
    <span class="sleep-title">Sleep <span class="sleep-range-label">Last 7 days</span></span>
    {#if duration}
      <span class="sleep-duration">{duration}</span>
    {/if}
  </div>
  <div class="sleep-inputs">
    <div class="sleep-field">
      <label class="sleep-label">Bedtime</label>
      <div class="sleep-input-wrap">
        <input type="time" class="sleep-time-input" class:sleep-time-empty={!bedtime} bind:value={bedtime} onchange={handleChange} />
        {#if !bedtime}
          <span class="sleep-time-placeholder">--:--</span>
        {/if}
      </div>
    </div>
    <div class="sleep-field">
      <label class="sleep-label">Wake up</label>
      <div class="sleep-input-wrap">
        <input type="time" class="sleep-time-input" class:sleep-time-empty={!wakeTime} bind:value={wakeTime} onchange={handleChange} />
        {#if !wakeTime}
          <span class="sleep-time-placeholder">--:--</span>
        {/if}
      </div>
    </div>
  </div>
  {#if chartData.length >= 2}
    <div class="sleep-chart-container">
      <MiniLineChart
        data={chartData}
        height={56}
        yMin={4}
        yMax={10}
        formatValue={(v) => `${v.toFixed(1)}h`}
      />
    </div>
  {:else if weekData.length > 0}
    <div class="sleep-chart-container">
      <span class="sleep-chart-empty">Graph appears after 2+ days of tracking</span>
    </div>
  {/if}
</div>

<style>
  .sleep-logger {
    border-radius: var(--radius-md);
    padding: var(--space-lg);
    background: var(--card-bg);
    border: 1px solid var(--border);
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

  .sleep-input-wrap {
    position: relative;
    height: 44px;
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    background: var(--card-bg);
    transition: border-color var(--ease-micro);
  }

  .sleep-input-wrap:focus-within {
    border-color: var(--text-tertiary);
  }

  .sleep-time-placeholder {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    padding: 0 12px;
    justify-content: center;
    font-family: var(--font-mono);
    font-size: 14px;
    color: var(--text-tertiary);
    pointer-events: none;
  }

  .sleep-time-input {
    position: absolute;
    inset: 0;
    border: none;
    border-radius: var(--radius-md);
    padding: 0 12px;
    text-align: center;
    background: transparent;
    color: var(--text);
    font-family: var(--font-mono);
    font-size: 14px;
    outline: none;
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    height: 100%;
  }

  .sleep-time-empty {
    color: transparent;
    -webkit-text-fill-color: transparent;
  }

  :global([data-theme='dark']) .sleep-time-input {
    color-scheme: dark;
  }

  .sleep-chart-container {
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px solid var(--border);
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
