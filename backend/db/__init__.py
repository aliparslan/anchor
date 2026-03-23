from db.base import get_db, init_db

from db.journal import (
    get_journal_dates,
    get_journal_entries_preview,
    get_journal_entry,
    append_journal_entry,
    save_journal_entry,
)

from db.focus import (
    get_pomodoro_sessions,
    save_pomodoro_session,
    get_pomodoro_total,
)

from db.habits import (
    get_habit_completions,
    toggle_habit,
    get_custom_habits,
    add_custom_habit,
    delete_custom_habit,
)

from db.health import (
    get_sleep_week,
    get_sleep_log,
    save_sleep_log,
    get_workout,
    toggle_workout,
    save_workout_note,
    get_mood,
    save_mood,
    get_water_today,
    increment_water,
    decrement_water,
    set_water,
    get_water_week,
)

from db.feed import (
    get_latest_hn_posts,
    save_hn_posts,
    get_latest_youtube_videos,
    save_youtube_videos,
    dismiss_video,
    get_dismissed_video_ids,
    get_reading_queue,
    save_to_reading_queue,
    mark_queue_item_read,
    delete_queue_item,
    delete_queue_item_by_hn_id,
    mark_queue_item_unread,
    seed_rss_feeds,
    get_rss_feeds,
    get_rss_items,
    save_rss_items,
    update_feed_fetched,
)

from db.mit import (
    get_mit,
    save_mit,
    toggle_mit,
)

from db.gratitude import (
    get_gratitudes,
    save_gratitude,
    get_random_gratitude,
)

from db.todos import (
    get_todos,
    create_todo,
    update_todo,
    complete_todo,
    undo_todo,
    delete_todo,
    reorder_todos,
)

from db.search import search_all

from db.stats import (
    get_habits_week,
    get_streaks,
    get_daily_summary,
    get_focus_month,
    get_streak,
    get_daily_score,
    get_weekly_review,
)

from db.settings import (
    get_setting,
    save_setting,
    save_push_subscription,
    delete_push_subscription,
    get_push_subscriptions,
)

