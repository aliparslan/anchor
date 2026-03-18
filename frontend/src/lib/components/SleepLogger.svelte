<script lang="ts">
  import { fetchSleepToday, saveSleep } from '$lib/api';

  let bedtime = $state('');
  let wakeTime = $state('');
  let saveTimeout: ReturnType<typeof setTimeout> | null = null;

  function computeDuration(): string {
    if (!bedtime || !wakeTime) return '';
    const [bh, bm] = bedtime.split(':').map(Number);
    const [wh, wm] = wakeTime.split(':').map(Number);
    let diff = (wh * 60 + wm) - (bh * 60 + bm);
    if (diff <= 0) diff += 24 * 60;
    const h = Math.floor(diff / 60);
    const m = diff % 60;
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  }

  function handleChange() {
    if (!bedtime || !wakeTime) return;
    if (saveTimeout) clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
      saveSleep(bedtime, wakeTime);
    }, 800);
  }

  $effect(() => {
    fetchSleepToday().then((data) => {
      bedtime = data?.bedtime || '';
      wakeTime = data?.wake_time || '';
    });
  });

  const duration = $derived(computeDuration());
</script>

<div class="sleep-logger">
  <div class="sleep-header">
    <span class="sleep-title">Sleep</span>
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
</div>

<style>
  .sleep-logger {
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    background: var(--card-bg);
    margin-bottom: 16px;
  }

  .sleep-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .sleep-title {
    font-family: var(--font-display);
    font-size: 14px;
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
    border-radius: 6px;
    padding: 8px 10px;
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-sans);
    font-size: 14px;
    outline: none;
  }

  .sleep-time-input:focus {
    border-color: var(--text-tertiary);
  }

  :global([data-theme='dark']) .sleep-time-input {
    color-scheme: dark;
  }
</style>
