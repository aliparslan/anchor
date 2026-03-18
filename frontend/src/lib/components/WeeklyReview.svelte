<script lang="ts">
  import { fetchWeeklyReview, type WeeklyReview } from '$lib/api';

  let review = $state<WeeklyReview | null>(null);
  let expanded = $state(new Date().getDay() === 0);

  const moodColors = ['', '#e04545', '#e68a3a', '#c4a06a', '#3b82f6', '#22c55e'];

  $effect(() => {
    fetchWeeklyReview().then((data) => (review = data));
  });
</script>

<div class="weekly-review">
  <button class="weekly-toggle" onclick={() => (expanded = !expanded)}>
    <span class="weekly-toggle-label">Weekly Review</span>
    <span class="weekly-toggle-arrow" class:weekly-expanded={expanded}>&rsaquo;</span>
  </button>
  {#if expanded && review}
    <div class="weekly-content">
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
      <div class="weekly-mood-row">
        <span class="weekly-stat-label">Mood</span>
        <div class="weekly-mood-dots">
          {#each review.mood_trend as m}
            <span
              class="weekly-mood-dot"
              style={m ? `background: ${moodColors[m]}; border-color: ${moodColors[m]}` : ''}
            ></span>
          {/each}
        </div>
      </div>
      {#if review.focus_per_day}
        <div class="weekly-focus-row">
          <span class="weekly-stat-label">Focus</span>
          <div class="weekly-focus-bars">
            {#each review.focus_per_day as hours}
              <div class="weekly-focus-bar-container">
                <div class="weekly-focus-bar" style="height: {Math.min(100, (hours / 4) * 100)}%"></div>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .weekly-review {
    border-radius: 10px;
    background: var(--card-bg);
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
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
    gap: 12px;
    animation: fadeSlideIn 0.3s ease;
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

  .weekly-mood-row {
    grid-column: 1 / -1;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .weekly-mood-dots {
    display: flex;
    gap: 6px;
  }

  .weekly-mood-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 1.5px solid var(--border);
    background: var(--bg-inset);
    transition: background 0.2s ease;
  }

  .weekly-focus-row {
    grid-column: 1 / -1;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .weekly-focus-bars {
    display: flex;
    gap: 6px;
    flex: 1;
    align-items: flex-end;
    height: 40px;
  }

  .weekly-focus-bar-container {
    flex: 1;
    height: 100%;
    display: flex;
    align-items: flex-end;
  }

  .weekly-focus-bar {
    width: 100%;
    border-radius: 3px 3px 0 0;
    background: var(--accent);
    min-height: 2px;
    transition: height 0.3s ease;
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
