<script lang="ts">
  import { fetchWeeklyReview, type WeeklyReview } from '$lib/api';
  import MiniBarChart from './charts/MiniBarChart.svelte';

  let review = $state<WeeklyReview | null>(null);
  let expanded = $state(new Date().getDay() === 0);

  const moodColors = ['', '#e04545', '#e68a3a', '#c4a06a', '#3b82f6', '#22c55e'];
  const moodLabels = ['', 'Awful', 'Low', 'Okay', 'Good', 'Great'];
  const dayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

  function refresh() {
    fetchWeeklyReview().then((data) => (review = data));
  }

  function toggle() {
    expanded = !expanded;
    if (expanded) refresh();
  }

  $effect(() => { refresh(); });

  const focusBarData = $derived(
    review?.focus_per_day?.map((hours, i) => ({
      label: dayLabels[i] || '',
      value: hours,
    })) ?? []
  );
</script>

<div class="weekly-review">
  <button class="weekly-toggle" onclick={toggle}>
    <span class="weekly-toggle-label">Weekly Review</span>
    {#if !expanded && review}
      <span class="weekly-toggle-preview">{review.focus_hours}h focus · {review.habit_rate.completed}/{review.habit_rate.total} habits</span>
    {/if}
    <span class="weekly-toggle-arrow" class:weekly-expanded={expanded}>&rsaquo;</span>
  </button>
  {#if expanded && review}
    <div class="weekly-content">
      <div class="weekly-stats">
        <div class="weekly-stat">
          <span class="weekly-stat-value">{review.focus_hours}h</span>
          <span class="weekly-stat-label">Focus</span>
        </div>
        <div class="weekly-stat">
          <span class="weekly-stat-value">{review.habit_rate.completed}/{review.habit_rate.total}</span>
          <span class="weekly-stat-label">Habits</span>
        </div>
        <div class="weekly-stat">
          <span class="weekly-stat-value">{review.mit_rate.completed}/{review.mit_rate.total}</span>
          <span class="weekly-stat-label">MITs done</span>
        </div>
        {#if review.avg_sleep_hours !== null}
          <div class="weekly-stat">
            <span class="weekly-stat-value">{review.avg_sleep_hours}h</span>
            <span class="weekly-stat-label">Avg sleep</span>
          </div>
        {/if}
      </div>

      {#if review.focus_per_day}
        <div class="weekly-chart-section">
          <span class="weekly-chart-label">Daily focus</span>
          <MiniBarChart
            data={focusBarData}
            max={6}
            height={72}
            goalLine={4}
            formatValue={(v) => `${v.toFixed(1)}h`}
          />
        </div>
      {/if}

      <div class="weekly-chart-section">
        <span class="weekly-chart-label">Mood</span>
        <div class="weekly-mood-row">
          {#each review.mood_trend as m, i}
            <div class="weekly-mood-col">
              <span
                class="weekly-mood-dot"
                class:weekly-mood-dot-empty={!m}
                style={m ? `background: ${moodColors[m]}; border-color: ${moodColors[m]}` : ''}
                title={m ? moodLabels[m] : 'No data'}
              ></span>
              <span class="weekly-mood-day">{dayLabels[i]}</span>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .weekly-review {
    border-radius: var(--radius-md);
    background: var(--card-bg);
    border: 1px solid var(--border);
    overflow: hidden;
  }

  .weekly-toggle {
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

  .weekly-toggle-preview {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-tertiary);
    font-weight: 400;
    margin-left: auto;
    margin-right: 8px;
  }

  .weekly-toggle-arrow {
    color: var(--text-tertiary);
    transition: transform 0.2s ease;
    font-size: 18px;
  }

  .weekly-expanded {
    transform: rotate(90deg);
  }

  .weekly-content {
    padding: 0 16px 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    animation: fadeSlideIn 0.3s ease;
  }

  .weekly-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
    gap: 12px;
  }

  .weekly-stat {
    text-align: center;
  }

  .weekly-stat-value {
    display: block;
    font-family: var(--font-mono);
    font-size: 18px;
    font-weight: 400;
    color: var(--text);
    letter-spacing: -0.01em;
  }

  .weekly-stat-label {
    font-size: 11px;
    color: var(--text-tertiary);
    font-family: var(--font-display);
  }

  .weekly-chart-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .weekly-chart-label {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .weekly-mood-row {
    display: flex;
    justify-content: space-between;
    gap: 4px;
  }

  .weekly-mood-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    flex: 1;
  }

  .weekly-mood-dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    border: 1.5px solid var(--border);
    background: var(--bg-inset);
    transition: all 0.2s ease;
  }

  .weekly-mood-dot-empty {
    opacity: 0.4;
  }

  .weekly-mood-day {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-tertiary);
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
