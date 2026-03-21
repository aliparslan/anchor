# Todo List Feature Design

## Overview

Add a todo list to Anchor with swipe gestures, a satisfying completion animation, and MIT integration. The Status page moves to a settings gear icon in the PageHeader, freeing a nav slot for the new Todos tab.

## Navigation Changes

**Before:** Home — Feed — [Note] — Track — Status
**After:** Home — Feed — [Note] — Todos — Track

- Status page becomes `/settings`, accessible via a gear icon (GearSix, phosphor duotone) in PageHeader next to the theme toggle
- Todos tab uses ListChecks (phosphor duotone) icon
- Route: `/todos/`

## Data Model

### Backend: `todos` table

```sql
CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    completed_at TEXT,        -- ISO timestamp, NULL if not completed
    position INTEGER NOT NULL, -- for manual reordering
    created_at TEXT NOT NULL,
    date TEXT NOT NULL         -- YYYY-MM-DD, the day the todo was created
);
```

- Completed todos: `completed_at IS NOT NULL`
- Cleanup: completed todos older than today are excluded from API responses (filtered on read, not deleted — keeps history if needed later)
- Position field enables drag-to-reorder (future enhancement)

### API Endpoints

```
GET    /api/todos              — returns today's active + today's completed todos
POST   /api/todos              — create a new todo { text: string }
PUT    /api/todos/:id          — update todo text { text: string }
POST   /api/todos/:id/complete — mark complete (sets completed_at)
POST   /api/todos/:id/undo     — undo completion (clears completed_at)
DELETE /api/todos/:id          — delete a todo (swipe-to-delete)
POST   /api/todos/reorder      — update positions { ids: number[] }
```

Todos response returns active items sorted by position, then completed items sorted by completed_at desc.

## Frontend Components

### TodoList.svelte (new component)

The main todo list, used on the `/todos/` page.

**Structure:**
- MIT section at top (uses existing MitInput component, already built)
- Divider or small spacing
- "Add todo" inline input (text field, appears on tap of + button, submits on Enter)
- Active todos list
- Completed todos list (grayed out, at bottom)

### TodoItem.svelte (new component)

Each individual todo row.

**Visual design:**
- Hollow circle on the left (thin `var(--border)` ring, ~20px diameter)
- Todo text to the right, DM Sans 14px
- Tap the circle to complete

**Completion circle:**
- Unchecked: hollow circle, 1px border `var(--border)`
- Checked: filled circle with `var(--accent)`, subtle scale-pop animation (scale 1 → 1.15 → 1 over 200ms)
- CSS transition on background-color and transform

**Completion behavior:**
1. Tap circle → circle fills with accent color (scale-pop)
2. After 300ms delay, text gets strikethrough animation (pseudo-element `::after` grows `width: 0 → 100%` over 300ms)
3. After another 400ms, the item fades to `opacity: 0.45` and slides down to the completed section
4. Completed items show: filled circle + struck-through text + gray

**Swipe gestures (touch events):**
- Swipe right (>80px threshold) → complete the todo
  - Item slides right with the swipe, accent-colored background revealed behind
  - On release past threshold, triggers completion
- Swipe left (>80px threshold) → delete the todo
  - Item slides left, red/warm background revealed behind
  - On release past threshold, item slides fully off-screen and is deleted
- Swipes < threshold snap back with spring animation
- Horizontal swipe detected when `deltaX > deltaY * 1.5` (prevents conflict with vertical scroll)

**Undo:**
- Tapping a completed todo's filled circle undoes it (clears completed_at, moves back to active list)

### Todos Page (`/todos/+page.svelte`)

```
<PageHeader title="Todos" />
<SectionHeader title="Priority" />
<MitInput />
<SectionHeader title="Tasks" />
<TodoList />
```

MIT stays as-is on the home page too (both views read/write the same backend data).

## Settings Page

### Route: `/settings/+page.svelte`

Move current Status page content here. Access via GearSix icon in PageHeader (all pages).

**PageHeader changes:**
- Add gear icon button next to theme toggle
- Links to `/settings`
- Uses `GearSix` phosphor icon, duotone weight, same size as theme toggle (18px)

## CSS

All new styles go in `app.css`. Key classes:
- `.todo-item` — the row container (position: relative for swipe)
- `.todo-circle` — the completion circle
- `.todo-circle-filled` — filled state
- `.todo-text` — the text with `::after` pseudo for strikethrough
- `.todo-text-done` — reduced opacity state
- `.todo-input` — inline add-todo input
- `.todo-completed-section` — wrapper for completed items at bottom

## Files to Create/Modify

**New files:**
- `frontend/src/lib/components/TodoList.svelte`
- `frontend/src/lib/components/TodoItem.svelte`
- `frontend/src/routes/todos/+page.svelte`
- `frontend/src/routes/settings/+page.svelte`
- `backend/db/todos.py`

**Modified files:**
- `backend/db/base.py` — add todos table to schema
- `backend/db/__init__.py` — re-export todo functions
- `backend/main.py` — add todo API routes
- `frontend/src/lib/api.ts` — add todo API functions + types
- `frontend/src/lib/components/PageHeader.svelte` — add gear icon
- `frontend/src/routes/+layout.svelte` — update nav tabs (Status → Todos, add settings route handling)
- `frontend/src/app.css` — todo styles, swipe styles
- `frontend/src/routes/+page.svelte` — no changes (MitInput already there)

**Deleted files:**
- `frontend/src/routes/status/+page.svelte` — moved to settings

## Interaction Summary

| Action | Gesture | Result |
|--------|---------|--------|
| Complete todo | Tap circle or swipe right | Fill circle, strikethrough animation, slide to bottom |
| Undo complete | Tap filled circle | Unfill, remove strike, move back to active |
| Delete todo | Swipe left | Slide off-screen, delete from DB |
| Add todo | Tap +, type, Enter | Appears at bottom of active list |
| Edit todo | Tap text | Inline edit (select all, save on blur/Enter) |
