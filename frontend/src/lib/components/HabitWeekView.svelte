<script lang="ts">
  import type { HabitsWeek } from '$lib/api';

  let { data = null }: { data: HabitsWeek | null } = $props();

  const habitLabels: Record<string, string> = {
    focus: 'Focus',
    workout: 'Workout',
    night_routine: 'Night Routine',
    sleep_tracked: 'Sleep',
    mood_logged: 'Mood'
  };

  function getHabitLabel(key: string): string {
    if (key.startsWith('custom:')) return key.slice(7);
    return habitLabels[key] || key;
  }

  function dayLabel(dateStr: string): string {
    const d = new Date(dateStr + 'T12:00:00');
    return ['S', 'M', 'T', 'W', 'T', 'F', 'S'][d.getDay()];
  }

  const today = new Date().toISOString().split('T')[0];

  let expanded = $state(false);

  const todayCompletions = $derived(() => {
    if (!data) return '';
    const todayIdx = data.dates.indexOf(today);
    if (todayIdx === -1) return '';
    const total = Object.keys(data.habits).length;
    const done = Object.values(data.habits).filter(days => days[todayIdx]).length;
    return `${done}/${total} today`;
  });
</script>

{#if data}
  <div class="week-view">
    <button class="week-toggle" onclick={() => expanded = !expanded}>
      <span class="week-toggle-label">Week</span>
      {#if !expanded && todayCompletions()}
        <span class="week-toggle-preview">{todayCompletions()}</span>
      {/if}
      <span class="week-toggle-arrow" class:week-toggle-expanded={expanded}>&rsaquo;</span>
    </button>
    {#if expanded}
      <div class="week-content">
        <div class="week-header">
          <span class="week-label"></span>
          {#each data.dates as d}
            <span class="week-day" class:week-today={d === today}>{dayLabel(d)}</span>
          {/each}
        </div>
        {#each Object.entries(data.habits) as [habit, days], hi}
          <div class="week-row" style="animation-delay: {hi * 50}ms">
            <span class="week-habit-name">{getHabitLabel(habit)}</span>
            {#each days as done, i}
              <span
                class="week-dot"
                class:week-dot-done={done}
                class:week-dot-future={data.dates[i] > today}
                style="animation-delay: {(hi * 7 + i) * 30}ms"
              ></span>
            {/each}
          </div>
        {/each}
      </div>
    {/if}
  </div>
{/if}

<style>
  .week-view {
    border-radius: 10px;
    background: var(--card-bg);
    margin-bottom: var(--space-widget);
    overflow: hidden;
  }

  .week-toggle {
    display: flex;
    width: 100%;
    justify-content: space-between;
    align-items: center;
    padding: 14px 16px;
    border: none;
    background: none;
    cursor: pointer;
    color: var(--text);
    font-family: var(--font-display);
    font-size: 14px;
    font-weight: 600;
  }

  .week-toggle-preview {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-tertiary);
    font-weight: 400;
    margin-left: auto;
    margin-right: 8px;
  }

  .week-toggle-arrow {
    color: var(--text-tertiary);
    transition: transform 0.2s ease;
    font-size: 18px;
  }

  .week-toggle-expanded {
    transform: rotate(90deg);
  }

  .week-content {
    padding: 0 16px 16px;
    animation: fadeSlideIn 0.3s ease;
  }

  .week-header,
  .week-row {
    display: grid;
    grid-template-columns: 90px repeat(7, 1fr);
    align-items: center;
    gap: 4px;
  }

  .week-row {
    padding: 6px 0;
    animation: fadeSlideIn 0.3s ease both;
  }

  .week-day {
    text-align: center;
    font-size: 11px;
    color: var(--text-tertiary);
    font-family: var(--font-display);
    font-weight: 500;
  }

  .week-today {
    color: var(--text);
    font-weight: 700;
  }

  .week-habit-name {
    font-size: 12px;
    color: var(--text-secondary);
    font-family: var(--font-display);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .week-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--bg-inset);
    border: 1.5px solid var(--border);
    margin: 0 auto;
    transition: all 0.2s ease;
    animation: dotFadeIn 0.4s ease both;
  }

  .week-dot-done {
    background: var(--accent);
    border-color: var(--accent);
  }

  .week-dot-future {
    opacity: 0.3;
  }

  .week-label {
    /* empty spacer to align grid */
  }

  @keyframes dotFadeIn {
    from {
      opacity: 0;
      transform: scale(0.5);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }

  @keyframes fadeSlideIn {
    from {
      opacity: 0;
      transform: translateY(4px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>
