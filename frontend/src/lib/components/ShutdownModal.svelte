<script lang="ts">
  import { fetchDaySummary, type DaySummary } from '$lib/api';
  import { Check } from 'phosphor-svelte';

  let { open = false, onclose }: { open: boolean; onclose: () => void } = $props();
  let summary = $state<DaySummary | null>(null);

  const habitLabels: Record<string, string> = {
    focus: 'Focus 4h',
    workout: 'Workout',
    night_routine: 'Night Routine',
    sleep_tracked: 'Sleep Tracked',
    mood_logged: 'Mood Logged'
  };

  $effect(() => {
    if (open) {
      fetchDaySummary().then((data) => (summary = data));
    }
  });

  function focusLabel(mins: number): string {
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    if (h === 0) return `${m}m`;
    if (m === 0) return `${h}h`;
    return `${h}h ${m}m`;
  }
</script>

<svelte:window onkeydown={(e) => { if (open && e.key === 'Escape') onclose(); }} />

{#if open}
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div class="shutdown-overlay" onclick={onclose}>
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div class="shutdown-modal" onclick={(e) => e.stopPropagation()}>
      <h2 class="shutdown-title">Today</h2>

      {#if summary}
        <div class="shutdown-sections">
          <!-- MIT -->
          <div class="shutdown-row">
            <div class="shutdown-check" class:shutdown-check-done={summary.mit?.completed}>
              {#if summary.mit?.completed}
                <Check size={12} weight="bold" />
              {/if}
            </div>
            <div class="shutdown-detail">
              <span class="shutdown-row-label">Priority</span>
              <span class="shutdown-row-value">{summary.mit?.text || 'Not set'}</span>
            </div>
          </div>

          <!-- Focus -->
          <div class="shutdown-row">
            <div class="shutdown-check" class:shutdown-check-done={summary.focus_minutes >= 240}>
              {#if summary.focus_minutes >= 240}
                <Check size={12} weight="bold" />
              {/if}
            </div>
            <div class="shutdown-detail">
              <span class="shutdown-row-label">Focus</span>
              <span class="shutdown-row-value">{focusLabel(summary.focus_minutes)}</span>
            </div>
          </div>

          <!-- Habits -->
          {#each summary.habits.filter(h => h.name !== 'focus') as habit}
            <div class="shutdown-row">
              <div class="shutdown-check" class:shutdown-check-done={habit.done}>
                {#if habit.done}
                  <Check size={12} weight="bold" />
                {/if}
              </div>
              <div class="shutdown-detail">
                <span class="shutdown-row-label">{habitLabels[habit.name] || habit.name}</span>
              </div>
            </div>
          {/each}

          <!-- Journal -->
          <div class="shutdown-row">
            <div class="shutdown-check" class:shutdown-check-done={summary.journal_written}>
              {#if summary.journal_written}
                <Check size={12} weight="bold" />
              {/if}
            </div>
            <div class="shutdown-detail">
              <span class="shutdown-row-label">Journal</span>
            </div>
          </div>
        </div>

        <button class="shutdown-close-btn" onclick={onclose}>Done</button>
      {:else}
        <p class="shutdown-loading">Loading...</p>
      {/if}
    </div>
  </div>
{/if}

<style>
  .shutdown-overlay {
    position: fixed;
    inset: 0;
    z-index: 200;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    animation: fadeIn 0.2s ease;
  }

  .shutdown-modal {
    background: var(--card-bg);
    border-radius: 14px;
    padding: 28px;
    max-width: 380px;
    width: 100%;
    animation: modalSlideUp 0.3s ease;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  }

  .shutdown-title {
    font-family: var(--font-display);
    font-size: 22px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 24px;
    letter-spacing: -0.02em;
    margin-top: 0;
  }

  .shutdown-sections {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 24px;
  }

  .shutdown-row {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .shutdown-check {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: 2px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    color: var(--bg);
    transition: all 0.2s ease;
  }

  .shutdown-check-done {
    background: var(--accent);
    border-color: var(--accent);
  }

  .shutdown-detail {
    flex: 1;
  }

  .shutdown-row-label {
    font-size: 13px;
    color: var(--text-secondary);
    font-family: var(--font-display);
    font-weight: 500;
  }

  .shutdown-row-value {
    font-size: 12px;
    color: var(--text-tertiary);
    display: block;
    margin-top: 2px;
  }

  .shutdown-close-btn {
    width: 100%;
    padding: 12px;
    border-radius: 8px;
    border: none;
    background: var(--accent);
    color: var(--bg);
    font-family: var(--font-display);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .shutdown-close-btn:hover {
    opacity: 0.9;
  }

  .shutdown-loading {
    text-align: center;
    color: var(--text-tertiary);
    font-size: 14px;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes modalSlideUp {
    from { opacity: 0; transform: translateY(20px) scale(0.97); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
</style>
