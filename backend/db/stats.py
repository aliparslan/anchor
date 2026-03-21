from datetime import datetime, date, timedelta, timezone

from db.base import get_db


async def get_habits_week(today: str) -> dict:
    today_date = date.fromisoformat(today)
    dates = [(today_date - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]

    db = await get_db()
    try:
        habits = {
            "focus": [],
            "workout": [],
            "night_routine": [],
            "sleep_tracked": [],
            "mood_logged": [],
        }
        for d in dates:
            # focus: pomodoro total >= 240
            cursor = await db.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
                (d,),
            )
            row = await cursor.fetchone()
            habits["focus"].append(int(row["total"]) >= 240)

            # workout
            cursor = await db.execute(
                "SELECT completed FROM workout_log WHERE date = ?", (d,)
            )
            row = await cursor.fetchone()
            habits["workout"].append(bool(row and row["completed"]))

            # night_routine
            cursor = await db.execute(
                "SELECT 1 FROM habit_completions WHERE date = ? AND habit = 'night_routine'",
                (d,),
            )
            row = await cursor.fetchone()
            habits["night_routine"].append(row is not None)

            # sleep_tracked
            cursor = await db.execute(
                "SELECT 1 FROM sleep_log WHERE date = ?", (d,)
            )
            row = await cursor.fetchone()
            habits["sleep_tracked"].append(row is not None)

            # mood_logged
            cursor = await db.execute(
                "SELECT 1 FROM mood_log WHERE date = ?", (d,)
            )
            row = await cursor.fetchone()
            habits["mood_logged"].append(row is not None)

        # Custom habits
        cursor = await db.execute("SELECT * FROM custom_habits ORDER BY created_at")
        custom_rows = await cursor.fetchall()
        for ch in custom_rows:
            habit_key = f"custom:{ch['name']}"
            habits[habit_key] = []
            for d in dates:
                cursor = await db.execute(
                    "SELECT 1 FROM habit_completions WHERE date = ? AND habit = ?",
                    (d, ch["name"]),
                )
                row = await cursor.fetchone()
                habits[habit_key].append(row is not None)

        return {"dates": dates, "habits": habits}
    finally:
        await db.close()


async def get_streaks(today: str) -> dict[str, int]:
    today_date = date.fromisoformat(today)
    db = await get_db()
    try:
        streaks = {}
        habit_checks = {
            "focus": "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
            "workout": "SELECT completed FROM workout_log WHERE date = ?",
            "night_routine": "SELECT 1 as v FROM habit_completions WHERE date = ? AND habit = 'night_routine'",
            "sleep_tracked": "SELECT 1 as v FROM sleep_log WHERE date = ?",
            "mood_logged": "SELECT 1 as v FROM mood_log WHERE date = ?",
        }
        for habit_name, query in habit_checks.items():
            count = 0
            d = today_date
            while True:
                ds = d.isoformat()
                cursor = await db.execute(query, (ds,))
                row = await cursor.fetchone()
                done = False
                if habit_name == "focus":
                    done = row is not None and int(row["total"]) >= 240
                elif habit_name == "workout":
                    done = row is not None and bool(row["completed"])
                else:
                    done = row is not None
                if done:
                    count += 1
                    d -= timedelta(days=1)
                else:
                    break
            streaks[habit_name] = count

        # Custom habit streaks
        cursor = await db.execute("SELECT * FROM custom_habits ORDER BY created_at")
        custom_rows = await cursor.fetchall()
        for ch in custom_rows:
            habit_key = f"custom:{ch['name']}"
            count = 0
            d = today_date
            while True:
                ds = d.isoformat()
                cursor = await db.execute(
                    "SELECT 1 FROM habit_completions WHERE date = ? AND habit = ?",
                    (ds, ch["name"]),
                )
                row = await cursor.fetchone()
                if row is not None:
                    count += 1
                    d -= timedelta(days=1)
                else:
                    break
            streaks[habit_key] = count

        return streaks
    finally:
        await db.close()


async def get_daily_summary(today: str) -> dict:
    db = await get_db()
    try:
        # MIT
        cursor = await db.execute(
            "SELECT text, completed FROM daily_mit WHERE date = ?", (today,)
        )
        mit_row = await cursor.fetchone()
        mit = {"text": mit_row["text"], "completed": bool(mit_row["completed"])} if mit_row else None

        # Focus minutes
        cursor = await db.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
            (today,),
        )
        row = await cursor.fetchone()
        focus_minutes = int(row["total"])

        # Habits
        cursor = await db.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
            (today,),
        )
        pom = await cursor.fetchone()
        focus_done = int(pom["total"]) >= 240

        cursor = await db.execute(
            "SELECT completed FROM workout_log WHERE date = ?", (today,)
        )
        w_row = await cursor.fetchone()
        workout_done = bool(w_row and w_row["completed"])

        cursor = await db.execute(
            "SELECT 1 FROM habit_completions WHERE date = ? AND habit = 'night_routine'",
            (today,),
        )
        nr_row = await cursor.fetchone()
        nr_done = nr_row is not None

        cursor = await db.execute(
            "SELECT 1 FROM sleep_log WHERE date = ?", (today,)
        )
        sl_row = await cursor.fetchone()
        sleep_tracked = sl_row is not None

        cursor = await db.execute(
            "SELECT 1 FROM mood_log WHERE date = ?", (today,)
        )
        ml_row = await cursor.fetchone()
        mood_logged = ml_row is not None

        habits_list = [
            {"name": "focus", "done": focus_done},
            {"name": "workout", "done": workout_done},
            {"name": "night_routine", "done": nr_done},
            {"name": "sleep_tracked", "done": sleep_tracked},
            {"name": "mood_logged", "done": mood_logged},
        ]

        # Custom habits
        cursor = await db.execute("SELECT * FROM custom_habits ORDER BY created_at")
        custom_rows = await cursor.fetchall()
        for ch in custom_rows:
            cursor = await db.execute(
                "SELECT 1 FROM habit_completions WHERE date = ? AND habit = ?",
                (today, ch["name"]),
            )
            ch_row = await cursor.fetchone()
            habits_list.append({"name": f"custom:{ch['name']}", "done": ch_row is not None})

        # Journal
        cursor = await db.execute(
            "SELECT 1 FROM journal_entries WHERE date = ? AND content != ''", (today,)
        )
        j_row = await cursor.fetchone()
        journal_written = j_row is not None

        # Mood
        cursor = await db.execute(
            "SELECT mood FROM mood_log WHERE date = ?", (today,)
        )
        mood_row = await cursor.fetchone()
        mood_val = mood_row["mood"] if mood_row else None

        # Sleep
        cursor = await db.execute(
            "SELECT bedtime, wake_time FROM sleep_log WHERE date = ?", (today,)
        )
        sleep_row = await cursor.fetchone()
        sleep_data = {"bedtime": sleep_row["bedtime"], "wake_time": sleep_row["wake_time"]} if sleep_row else None

        # Workout
        cursor = await db.execute(
            "SELECT completed, note FROM workout_log WHERE date = ?", (today,)
        )
        wo_row = await cursor.fetchone()
        workout_data = {"completed": bool(wo_row["completed"]), "note": wo_row["note"]} if wo_row else None

        return {
            "mit": mit,
            "focus_minutes": focus_minutes,
            "habits": habits_list,
            "journal_written": journal_written,
            "mood": mood_val,
            "sleep": sleep_data,
            "workout": workout_data,
        }
    finally:
        await db.close()


async def get_focus_month(today_str: str) -> list[dict]:
    """Get daily focus minutes for last 30 days."""
    today = date.fromisoformat(today_str)
    start = (today - timedelta(days=29)).isoformat()
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT date, COALESCE(SUM(duration_minutes), 0) as minutes
               FROM pomodoro_sessions
               WHERE date >= ? AND date <= ?
               GROUP BY date
               ORDER BY date ASC""",
            (start, today_str),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_streak(today_str: str) -> int:
    """Count consecutive days with all core tasks done."""
    db = await get_db()
    try:
        streak = 0
        current = date.fromisoformat(today_str)
        while True:
            d = current.isoformat()
            # MIT completed
            mit = await db.execute("SELECT completed FROM daily_mit WHERE date = ?", (d,))
            mit_row = await mit.fetchone()
            if not mit_row or not mit_row["completed"]:
                break
            # Focus >= 240 min
            pom = await db.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?", (d,)
            )
            pom_row = await pom.fetchone()
            if pom_row["total"] < 240:
                break
            # Journal written
            j = await db.execute("SELECT content FROM journal_entries WHERE date = ?", (d,))
            j_row = await j.fetchone()
            if not j_row or not j_row["content"].strip():
                break
            streak += 1
            current -= timedelta(days=1)
        return streak
    finally:
        await db.close()


async def get_daily_score(today_str: str) -> dict:
    """Compute daily score 0-100."""
    db = await get_db()
    try:
        score = 0
        breakdown = {}

        # MIT: 25 pts
        mit = await db.execute("SELECT completed FROM daily_mit WHERE date = ?", (today_str,))
        mit_row = await mit.fetchone()
        mit_pts = 25 if (mit_row and mit_row["completed"]) else 0
        breakdown["mit"] = mit_pts
        score += mit_pts

        # Focus: 25 pts (proportional to 240 min)
        pom = await db.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
            (today_str,),
        )
        pom_row = await pom.fetchone()
        focus_mins = pom_row["total"]
        focus_pts = min(25, round(focus_mins / 240 * 25))
        breakdown["focus"] = focus_pts
        score += focus_pts

        # Habits: 25 pts (proportional) -- count ALL habits including auto-tracked
        done_habits = 0
        total_habits = 5  # focus, workout, night_routine, sleep_tracked, mood_logged

        # Auto: focus achieved (>= 240 min)
        if focus_mins >= 240:
            done_habits += 1
        # Auto: workout
        wo = await db.execute("SELECT completed FROM workout_log WHERE date = ?", (today_str,))
        wo_row = await wo.fetchone()
        if wo_row and wo_row["completed"]:
            done_habits += 1
        # Manual: night_routine (in habit_completions)
        nr = await db.execute("SELECT 1 FROM habit_completions WHERE date = ? AND habit = 'night_routine'", (today_str,))
        if await nr.fetchone():
            done_habits += 1
        # Auto: sleep tracked
        sl = await db.execute("SELECT 1 FROM sleep_log WHERE date = ?", (today_str,))
        if await sl.fetchone():
            done_habits += 1
        # Auto: mood logged
        mood_check = await db.execute("SELECT 1 FROM mood_log WHERE date = ?", (today_str,))
        if await mood_check.fetchone():
            done_habits += 1
        # Custom habits
        custom_cursor = await db.execute("SELECT COUNT(*) as c FROM custom_habits")
        custom_row = await custom_cursor.fetchone()
        total_habits += custom_row["c"]
        custom_done = await db.execute(
            "SELECT COUNT(*) as c FROM habit_completions WHERE date = ? AND habit != 'night_routine'", (today_str,)
        )
        custom_done_row = await custom_done.fetchone()
        done_habits += custom_done_row["c"]

        habit_pts = min(25, round(done_habits / max(total_habits, 1) * 25))
        breakdown["habits"] = habit_pts
        score += habit_pts

        # Journal: 15 pts
        j = await db.execute("SELECT content FROM journal_entries WHERE date = ?", (today_str,))
        j_row = await j.fetchone()
        journal_pts = 15 if (j_row and j_row["content"].strip()) else 0
        breakdown["journal"] = journal_pts
        score += journal_pts

        # Mood: 10 pts
        m = await db.execute("SELECT mood FROM mood_log WHERE date = ?", (today_str,))
        m_row = await m.fetchone()
        mood_pts = 10 if m_row else 0
        breakdown["mood"] = mood_pts
        score += mood_pts

        return {"score": score, "breakdown": breakdown}
    finally:
        await db.close()


async def get_weekly_review(today: str) -> dict:
    today_date = date.fromisoformat(today)
    dates = [(today_date - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    start_date = dates[0]
    end_date = dates[-1]

    db = await get_db()
    try:
        # Focus hours
        cursor = await db.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date >= ? AND date <= ?",
            (start_date, end_date),
        )
        row = await cursor.fetchone()
        focus_hours = round(int(row["total"]) / 60, 1)

        # Habit rate
        completed_count = 0
        total_count = 5 * 7
        for d in dates:
            cursor = await db.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
                (d,),
            )
            r = await cursor.fetchone()
            if int(r["total"]) >= 240:
                completed_count += 1

            cursor = await db.execute(
                "SELECT completed FROM workout_log WHERE date = ?", (d,)
            )
            r = await cursor.fetchone()
            if r and r["completed"]:
                completed_count += 1

            cursor = await db.execute(
                "SELECT 1 FROM habit_completions WHERE date = ? AND habit = 'night_routine'",
                (d,),
            )
            if await cursor.fetchone():
                completed_count += 1

            cursor = await db.execute(
                "SELECT 1 FROM sleep_log WHERE date = ?", (d,)
            )
            if await cursor.fetchone():
                completed_count += 1

            cursor = await db.execute(
                "SELECT 1 FROM mood_log WHERE date = ?", (d,)
            )
            if await cursor.fetchone():
                completed_count += 1

        # Mood trend
        mood_trend = []
        for d in dates:
            cursor = await db.execute(
                "SELECT mood FROM mood_log WHERE date = ?", (d,)
            )
            r = await cursor.fetchone()
            mood_trend.append(r["mood"] if r else None)

        # MIT rate
        cursor = await db.execute(
            "SELECT COUNT(*) as total FROM daily_mit WHERE date >= ? AND date <= ?",
            (start_date, end_date),
        )
        r = await cursor.fetchone()
        mit_total = int(r["total"])

        cursor = await db.execute(
            "SELECT COUNT(*) as total FROM daily_mit WHERE date >= ? AND date <= ? AND completed = 1",
            (start_date, end_date),
        )
        r = await cursor.fetchone()
        mit_completed = int(r["total"])

        # Avg sleep hours
        cursor = await db.execute(
            "SELECT bedtime, wake_time FROM sleep_log WHERE date >= ? AND date <= ?",
            (start_date, end_date),
        )
        sleep_rows = await cursor.fetchall()
        avg_sleep = None
        if sleep_rows:
            total_hours = 0.0
            valid_count = 0
            for sr in sleep_rows:
                try:
                    bt = datetime.strptime(sr["bedtime"], "%H:%M")
                    wt = datetime.strptime(sr["wake_time"], "%H:%M")
                    diff = (wt - bt).total_seconds() / 3600
                    if diff < 0:
                        diff += 24  # crossed midnight
                    total_hours += diff
                    valid_count += 1
                except (ValueError, TypeError):
                    pass
            if valid_count > 0:
                avg_sleep = round(total_hours / valid_count, 1)

        # Focus per day
        focus_per_day = []
        for d in dates:
            cursor = await db.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
                (d,),
            )
            r = await cursor.fetchone()
            focus_per_day.append(round(int(r["total"]) / 60, 1))

        return {
            "focus_hours": focus_hours,
            "habit_rate": {"completed": completed_count, "total": total_count},
            "mood_trend": mood_trend,
            "mit_rate": {"completed": mit_completed, "total": mit_total},
            "avg_sleep_hours": avg_sleep,
            "focus_per_day": focus_per_day,
        }
    finally:
        await db.close()
