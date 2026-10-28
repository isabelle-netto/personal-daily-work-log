
from datetime import date, datetime
from zoneinfo import ZoneInfo
import hmac
import time
import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Daily Work Log | Personal Workspace",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
:root { color-scheme: light; }
html, body, [class*="css"]  { font-family: Inter, Segoe UI, Arial, sans-serif; }
[data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: linear-gradient(180deg, #F7F9FC 0%, #EEF3F9 100%);
    color: #17324D;
}
[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E6ECF3;
}
.block-container {
    max-width: 1180px;
    padding-top: 2.2rem;
    padding-bottom: 4rem;
}

h1, h2, h3 {
    color: #15324B !important;
    letter-spacing: -0.02em;
}
h1 { font-weight: 800 !important; }
p, label, .stMarkdown, .stCaption { color: #49627B; }

/* Hero / intro cards */
.worklog-hero {
    background: linear-gradient(135deg, #FFFFFF 0%, #F4F8FC 100%);
    border: 1px solid #E4EBF3;
    border-radius: 20px;
    padding: 1.35rem 1.45rem;
    box-shadow: 0 8px 24px rgba(16, 42, 67, 0.05);
    margin-bottom: 1rem;
}
.worklog-hero .eyebrow {
    font-size: 0.8rem;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: #5D7690;
    font-weight: 700;
    margin-bottom: .35rem;
}
.worklog-hero .hero-title {
    font-size: 2rem;
    font-weight: 800;
    color: #15324B;
    margin-bottom: .35rem;
}
.worklog-hero .hero-sub {
    font-size: 1rem;
    color: #4F677F;
    line-height: 1.6;
}
.mini-note {
    background: #FFFFFF;
    border: 1px solid #E6ECF3;
    border-radius: 14px;
    padding: .85rem 1rem;
    margin: .3rem 0 .8rem 0;
}

/* Metrics / containers */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E4EBF3;
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 5px 18px rgba(18, 45, 75, 0.045);
}
[data-testid="stMetricLabel"] { color: #657C94; }
[data-testid="stMetricValue"] { color: #173B62; }

[data-testid="stForm"], [data-testid="stExpander"], [data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,.82);
    border: 1px solid #E4EBF3;
    border-radius: 16px;
}

/* Tabs */
[data-baseweb="tab-list"] {
    gap: 10px;
    background: transparent;
    border-bottom: 1px solid #E1E8F0;
    padding-bottom: .3rem;
}
button[data-baseweb="tab"] {
    background: #F3F7FB !important;
    border: 1px solid #E3EAF2 !important;
    border-radius: 999px !important;
    color: #35516C !important;
    font-weight: 700 !important;
    padding: .55rem 1rem !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: #174A7E !important;
    color: #FFFFFF !important;
    border-color: #174A7E !important;
}

/* Inputs: style the actual elements, not only BaseWeb wrappers. */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stNumberInput"] input,
[data-baseweb="textarea"] textarea,
[data-baseweb="input"] input,
textarea {
    background-color: #FFFFFF !important;
    color: #17324D !important;
    -webkit-text-fill-color: #17324D !important;
    caret-color: #17324D !important;
    color-scheme: light !important;
    border-radius: 10px !important;
}
[data-testid="stTextArea"] [data-baseweb="textarea"],
[data-testid="stTextArea"] [data-baseweb="textarea"] > div,
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stDateInput"] [data-baseweb="input"],
[data-testid="stTextInputRootElement"],
[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #17324D !important;
    border-color: #CBD7E3 !important;
    color-scheme: light !important;
}
[data-baseweb="select"] input,
[data-baseweb="select"] span,
[data-baseweb="select"] div[role="combobox"] {
    color: #17324D !important;
    -webkit-text-fill-color: #17324D !important;
}
[data-testid="stTextArea"] textarea::placeholder,
[data-baseweb="input"] input::placeholder,
textarea::placeholder,
input::placeholder {
    color: #8196AC !important;
    -webkit-text-fill-color: #8196AC !important;
    opacity: 1 !important;
}
[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextInput"] input:focus {
    outline: 2px solid #9DBBDC !important;
    outline-offset: -2px;
}

/* Multiselect tags */
[data-baseweb="tag"] {
    background: #EAF2FA !important;
    color: #1E4A74 !important;
    border-radius: 999px !important;
}

/* Buttons */
.stButton button[kind="primary"],
.stDownloadButton button[kind="primary"],
.stFormSubmitButton button[kind="primary"] {
    background: #174A7E !important;
    border: 1px solid #174A7E !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
}
.stButton button,
.stDownloadButton button,
.stFormSubmitButton button {
    border-radius: 10px !important;
}
.stButton button:hover,
.stDownloadButton button:hover,
.stFormSubmitButton button:hover {
    filter: brightness(1.02);
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #E4EBF3;
    border-radius: 14px;
    overflow: hidden;
    background: #FFFFFF;
}

/* Misc */
hr { border-color: #E3EAF2; }
</style>
""", unsafe_allow_html=True)


def local_today():
    return datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date()


def login_gate():
    if st.session_state.get("worklog_authenticated", False):
        return
    try:
        password = str(st.secrets["APP_PASSWORD"])
    except (KeyError, FileNotFoundError):
        st.error("App password is not configured. Add APP_PASSWORD to Streamlit → App settings → Secrets.")
        st.stop()
    if len(password) < 12:
        st.error("APP_PASSWORD must contain at least 12 characters. Update it in Streamlit Secrets.")
        st.stop()

    st.markdown("""
    <div class="worklog-hero">
        <div class="eyebrow">Personal workspace / private access</div>
        <div class="hero-title">Daily Work Log</div>
        <div class="hero-sub">A simple, organised space to plan your work, follow up unfinished tasks, and maintain a clear record of what you’ve done.</div>
    </div>
    """, unsafe_allow_html=True)

    lock_until = st.session_state.get("worklog_lock_until", 0)
    if time.time() < lock_until:
        st.warning("Too many attempts. Please try again in a few minutes.")
        st.stop()

    with st.container(border=True):
        st.subheader("Sign in")
        st.caption("Enter your workspace password to continue.")
        with st.form("login_form", clear_on_submit=True):
            entered = st.text_input("Workspace password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Unlock work log", type="primary", use_container_width=True)
        if submitted:
            if hmac.compare_digest(entered.encode(), password.encode()):
                st.session_state["worklog_authenticated"] = True
                st.session_state["worklog_attempts"] = 0
                st.rerun()
            else:
                attempts = st.session_state.get("worklog_attempts", 0) + 1
                st.session_state["worklog_attempts"] = attempts
                if attempts >= 5:
                    st.session_state["worklog_lock_until"] = time.time() + 300
                    st.session_state["worklog_attempts"] = 0
                    st.warning("Too many attempts. Please try again in five minutes.")
                else:
                    st.error("Incorrect password.")
        st.caption("Your records are stored in your personal Supabase project.")
    st.stop()


login_gate()

with st.sidebar:
    st.markdown("### Daily Work Log")
    st.caption("Personal workspace")
    if st.button("🔒 Sign out", use_container_width=True):
        st.session_state["worklog_authenticated"] = False
        st.rerun()
    st.divider()
    st.caption("Stored securely in Supabase")

STATUSES = ["Pending", "Completed", "Not Completed"]


@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SECRET_KEY"])


def add_task(task_date, task):
    get_supabase().table("work_tasks").insert({"task_date": task_date.isoformat(), "task": task.strip()}).execute()


def update_task(task_id, task_date, task, status, remark, *, progress_date=None, previous_status=None, previous_remark=None):
    """Save task and append a dated progress entry when status/remark changes.

    Existing remarks remain available in work_tasks; the timeline is append-only.
    """
    client = get_supabase()
    note = (remark or "").strip()
    # Every press of Save progress produces a dated history entry.
    # Write history before updating the task so a missing history table
    # cannot silently overwrite the previous remark.
    client.table("work_task_updates").insert({
            "task_id": int(task_id),
            "update_date": (progress_date or local_today()).isoformat(),
            "status": status,
        "note": note,
    }).execute()

    client.table("work_tasks").update({
        "task_date": task_date.isoformat(),
        "task": task.strip(),
        "status": status,
        "remark": note,
    }).eq("id", int(task_id)).execute()


def read_updates():
    rows = []
    offset = 0
    while True:
        batch = (get_supabase().table("work_task_updates")
                 .select("id,task_id,update_date,status,note,created_at")
                 .order("id", desc=True)
                 .range(offset, offset + 999).execute().data or [])
        rows.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return pd.DataFrame(rows, columns=["id", "task_id", "update_date", "status", "note", "created_at"])


def show_timeline(task_id, updates):
    history = updates[updates["task_id"] == int(task_id)].copy()
    if history.empty:
        st.caption("No dated follow-ups yet. Your next update will appear here.")
        return
    history = history.sort_values(["update_date", "id"], ascending=[False, False])
    for event in history.itertuples(index=False):
        day_label = date.fromisoformat(event.update_date).strftime("%d %b %Y")
        st.markdown(f"**{day_label} · {event.status}**")
        if event.note:
            st.write(event.note)
        else:
            st.caption("Status updated (no remark).")


def delete_task(task_id):
    get_supabase().table("work_tasks").delete().eq("id", int(task_id)).execute()


def read_tasks():
    rows = []
    offset = 0
    while True:
        batch = (
            get_supabase().table("work_tasks")
            .select("id,task_date,task,status,remark,created_at,updated_at")
            .order("task_date", desc=True)
            .order("id", desc=True)
            .range(offset, offset + 999)
            .execute()
            .data
            or []
        )
        rows.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return pd.DataFrame(rows, columns=["id", "task_date", "task", "status", "remark", "created_at", "updated_at"])


st.markdown(f"""
<div class="worklog-hero">
    <div class="eyebrow">Personal workspace / productivity & reporting</div>
    <div class="hero-title">Daily Work Log</div>
    <div class="hero-sub">Plan your day, carry unfinished work forward with ease, and build clean reports without having to reconstruct everything at the end of the month.</div>
</div>
""", unsafe_allow_html=True)

try:
    all_tasks = read_tasks()
    all_updates = read_updates()
except Exception:
    st.error("Could not connect to Supabase. Check your Streamlit secrets and database setup.")
    st.caption("Run progress_history_setup.sql in Supabase first, then confirm table permissions and Streamlit Secrets.")
    st.stop()

if all_tasks.empty:
    all_tasks = pd.DataFrame(columns=["id", "task_date", "task", "status", "remark", "created_at", "updated_at"])

today_iso = local_today().isoformat()
today_tasks = all_tasks[all_tasks["task_date"] == today_iso]
today_total = len(today_tasks)
today_completed = int((today_tasks["status"] == "Completed").sum())
today_pending = int((today_tasks["status"] == "Pending").sum())
today_unfinished = int((today_tasks["status"] == "Not Completed").sum())
pending_all = all_tasks[all_tasks["status"] == "Pending"].copy()

st.caption(f"TODAY  ·  {local_today().strftime('%A, %d %B %Y')}")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Tasks today", today_total)
k2.metric("Completed", today_completed)
k3.metric("Open pending (all dates)", len(pending_all))
k4.metric("Not completed", today_unfinished)

st.markdown("""
<div class="mini-note"><strong>How this works:</strong> Add your tasks for the day, review them later, and use <strong>Pending tasks</strong> as your ongoing follow-up page for unfinished work from any date.</div>
""", unsafe_allow_html=True)

tab_pending, tab_add, tab_update, tab_report = st.tabs([
    "⏳  Pending tasks",
    "＋  Add tasks",
    "✓  Daily review",
    "▤  Reports & history",
])

with tab_pending:
    st.subheader("Your open tasks")
    st.write("Every unfinished task stays here, regardless of when you added it. Update it whenever you make progress; it disappears only when you change its status.")
    left, right = st.columns([3, 1])
    with left:
        pending_search = st.text_input("Find an open task", placeholder="Search by task or remark...", key="pending_search")
    with right:
        pending_order = st.selectbox("Sort by", ["Oldest first", "Newest first"], key="pending_order")

    pending_view = pending_all.copy()
    if pending_search.strip():
        q = pending_search.strip()
        pending_view = pending_view[
            pending_view["task"].str.contains(q, case=False, regex=False, na=False)
            | pending_view["remark"].fillna("").str.contains(q, case=False, regex=False, na=False)
        ]
    pending_view = pending_view.sort_values(["task_date", "id"], ascending=(pending_order == "Oldest first"))
    st.caption(f"{len(pending_view)} open task(s) shown · {len(pending_all)} open in total")

    if pending_view.empty:
        st.success("No pending tasks found. You are all caught up!" if pending_all.empty else "No tasks match that search.")
    else:
        for item in pending_view.itertuples(index=False):
            original_date = date.fromisoformat(item.task_date)
            days_old = (local_today() - original_date).days
            age = f"{days_old} day(s) old" if days_old > 0 else "Added today" if days_old == 0 else "Upcoming"
            with st.container(border=True):
                st.markdown(f"#### {item.task}")
                st.caption(f"Originally planned: {original_date.strftime('%d %b %Y')}  ·  {age}")
                if isinstance(item.remark, str) and item.remark.strip():
                    st.info(f"Latest remark: {item.remark}")
                with st.expander("📅 View progress history"):
                    show_timeline(item.id, all_updates)
                with st.form(f"pending_form_{item.id}"):
                    new_status = st.selectbox(
                        "Update status",
                        STATUSES,
                        index=STATUSES.index(item.status) if item.status in STATUSES else 0,
                        key=f"pending_status_{item.id}",
                    )
                    progress_day = st.date_input(
                        "Date of this progress update",
                        value=local_today(),
                        format="DD/MM/YYYY",
                        key=f"pending_progress_date_{item.id}",
                        help="Defaults to today; you can backdate it if reporting an earlier follow-up.",
                    )
                    new_remark = st.text_area(
                        "Progress note / remark (optional)",
                        value=item.remark or "",
                        key=f"pending_remark_{item.id}",
                        height=110,
                        placeholder="e.g. Followed up today; still awaiting approval",
                    )
                    save_pending = st.form_submit_button("Save progress", type="primary")
                    if save_pending:
                        try:
                            update_task(
                                item.id, original_date, item.task, new_status, new_remark,
                                progress_date=progress_day,
                                previous_status=item.status,
                                previous_remark=item.remark,
                            )
                            st.success("Progress updated.")
                            st.rerun()
                        except Exception:
                            st.error("Could not save your update. Please try again.")
                st.caption("Tip: Keep the status Pending if the work is still open, and update the remark as you make progress.")

with tab_add:
    st.subheader("Add a task or goal")
    st.write("Enter one task at a time for clearer tracking. Every new task starts as Pending.")
    with st.form("new_task_form", clear_on_submit=True):
        task_date = st.date_input("Date", value=local_today(), format="DD/MM/YYYY")
        task = st.text_area(
            "Task / goal for the day",
            placeholder="e.g. Prepare the stakeholder outreach report",
            height=110,
        )
        submitted = st.form_submit_button("Save task", type="primary")
        if submitted:
            if not task.strip():
                st.error("Please type a task before saving.")
            else:
                add_task(task_date, task)
                st.success("Task saved.")
                st.rerun()
    st.info("Tip: Smaller, separate tasks make your reports more accurate and easier to review later.")

with tab_update:
    st.subheader("Review your day")
    day = st.date_input("Choose the date to update", value=local_today(), format="DD/MM/YYYY", key="update_day")
    day_tasks = all_tasks[all_tasks["task_date"] == day.isoformat()]
    if day_tasks.empty:
        st.info("No tasks found for this date. Add one in the Add Tasks tab.")
    else:
        st.caption(f"{len(day_tasks)} task(s) on {day.strftime('%d %B %Y')}")
        for item in day_tasks.itertuples(index=False):
            with st.expander(f"{item.status}  |  {item.task[:110]}", expanded=(item.status == "Pending")):
                with st.form(f"edit_task_{item.id}"):
                    new_date = st.date_input(
                        "Date",
                        value=date.fromisoformat(item.task_date),
                        format="DD/MM/YYYY",
                        key=f"date_{item.id}",
                    )
                    new_task = st.text_area("Task / goal", value=item.task, key=f"task_{item.id}", height=100)
                    status = st.selectbox(
                        "End-of-day outcome",
                        STATUSES,
                        index=STATUSES.index(item.status),
                        key=f"status_{item.id}",
                    )
                    progress_day = st.date_input(
                        "Date of this update",
                        value=local_today(),
                        format="DD/MM/YYYY",
                        key=f"review_progress_date_{item.id}",
                    )
                    remark = st.text_area(
                        "Remark (optional)",
                        value=item.remark,
                        placeholder="e.g. Completed and sent to manager; or postponed awaiting approval.",
                        key=f"remark_{item.id}",
                        height=100,
                    )
                    save = st.form_submit_button("Save update", type="primary")
                    if save:
                        if not new_task.strip():
                            st.error("The task description cannot be empty.")
                        else:
                            update_task(
                                item.id, new_date, new_task, status, remark,
                                progress_date=progress_day,
                                previous_status=item.status,
                                previous_remark=item.remark,
                            )
                            st.success("Update saved.")
                            st.rerun()
                with st.expander("📅 View progress history"):
                    show_timeline(item.id, all_updates)
                with st.popover("Delete this task"):
                    st.warning("This deletion cannot be undone.")
                    if st.button("Confirm delete", key=f"delete_{item.id}"):
                        delete_task(item.id)
                        st.rerun()

with tab_report:
    st.subheader("Work report & history")
    today = local_today()
    default_start = today.replace(day=1)
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 2])
        with c1:
            start = st.date_input("From date", value=default_start, format="DD/MM/YYYY", key="filter_start")
        with c2:
            end = st.date_input("To date", value=today, format="DD/MM/YYYY", key="filter_end")
        with c3:
            selected_statuses = st.multiselect("Task status", STATUSES, default=STATUSES)
        search = st.text_input("Search tasks or remarks", placeholder="Search by keyword…")

    if start > end:
        st.error("The From date must be on or before the To date.")
    else:
        filtered = all_tasks[
            (all_tasks["task_date"] >= start.isoformat())
            & (all_tasks["task_date"] <= end.isoformat())
            & (all_tasks["status"].isin(selected_statuses))
        ].copy()
        if search.strip():
            filtered = filtered[
                filtered["task"].str.contains(search.strip(), case=False, regex=False, na=False)
                | filtered["remark"].fillna("").str.contains(search.strip(), case=False, regex=False, na=False)
            ]

        counts = filtered["status"].value_counts()
        total = len(filtered)
        completed = int(counts.get("Completed", 0))
        pending = int(counts.get("Pending", 0))
        not_completed = int(counts.get("Not Completed", 0))
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total tasks", total)
        m2.metric("Completed", completed)
        m3.metric("Not completed", not_completed)
        m4.metric("Pending", pending)
        m5.metric("Completion rate", f"{completed / total:.0%}" if total else "—")
        st.caption("Completion rate = completed tasks divided by all tasks matching the filters, including pending tasks.")

        if filtered.empty:
            st.info("There are no tasks matching these filters.")
        else:
            display = filtered[["task_date", "task", "status", "remark"]].rename(
                columns={
                    "task_date": "Date",
                    "task": "Task / Goal",
                    "status": "Outcome",
                    "remark": "Remark",
                }
            )
            display["Date"] = pd.to_datetime(display["Date"]).dt.strftime("%d/%m/%Y")
            st.dataframe(display, use_container_width=True, hide_index=True)

            csv = display.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "⬇️ Download filtered CSV report",
                data=csv,
                file_name=f"work_log_{start.isoformat()}_to_{end.isoformat()}.csv",
                mime="text/csv",
                type="primary",
            )

            st.markdown("#### Dated progress history")
            st.caption("Follow-ups are tracked by the date you recorded them, even when the original task was created on an earlier day.")
            related = all_updates[
                (all_updates["update_date"] >= start.isoformat())
                & (all_updates["update_date"] <= end.isoformat())
            ].copy()
            if related.empty:
                st.caption("No recorded progress updates within the selected date range.")
            else:
                related = related.merge(all_tasks[["id", "task"]], left_on="task_id", right_on="id", how="left")
                timeline_display = related[["update_date", "task", "status", "note"]].rename(
                    columns={"update_date": "Update date", "task": "Task", "status": "Status", "note": "Progress note"}
                )
                st.dataframe(timeline_display, hide_index=True, use_container_width=True)
                st.download_button(
                    "Download dated progress history (CSV)",
                    timeline_display.to_csv(index=False).encode("utf-8-sig"),
                    file_name=f"progress_history_{start.isoformat()}_to_{end.isoformat()}.csv",
                    mime="text/csv",
                )

        st.markdown("#### Daily activity report — written breakdown")
        st.caption(
            "Organised by the date work was started or progress was recorded, not just the original task date. "
            "Includes follow-ups for tasks started before the selected reporting period. "
            "Uses all task statuses; the status filter above applies to the summary table."
        )
        # Build a dated activity ledger. Start entries are separate from each
        # follow-up so work done on later days appears on those actual dates.
        activities = []
        for task_row in all_tasks.itertuples(index=False):
            if start.isoformat() <= task_row.task_date <= end.isoformat():
                activities.append({
                    "date": task_row.task_date, "task_id": int(task_row.id),
                    "task": str(task_row.task), "type": "started", "note": "",
                    "status": "", "order": 0,
                })
        for event in all_updates.itertuples(index=False):
            if start.isoformat() <= event.update_date <= end.isoformat():
                activities.append({
                    "date": event.update_date, "task_id": int(event.task_id),
                    "task": "", "type": "progress", "note": str(event.note or ""),
                    "status": str(event.status), "order": int(event.id),
                })
        tasks_by_id = {int(t.id): str(t.task) for t in all_tasks.itertuples(index=False)}
        activities.sort(key=lambda x: (x["date"], x["task_id"], x["type"] != "started", x["order"]))
        report_blocks = ["DAILY WORK ACTIVITY REPORT", f"Reporting period: {start.strftime('%d %B %Y')} – {end.strftime('%d %B %Y')}", ""]
        by_day = {}
        for activity in activities:
            by_day.setdefault(activity["date"], []).append(activity)
        for day_str, day_items in by_day.items():
            report_blocks.append(date.fromisoformat(day_str).strftime("%A, %d %B %Y"))
            report_blocks.append("-" * 45)
            by_task = {}
            for entry in day_items:
                by_task.setdefault(entry["task_id"], []).append(entry)
            for task_id, task_events in by_task.items():
                task_name = tasks_by_id.get(task_id, "Task no longer available")
                report_blocks.append(f"{task_name}")
                for entry in task_events:
                    if entry["type"] == "started":
                        report_blocks.append("  Work planned/started on this date.")
                    else:
                        note = entry["note"].strip()
                        if note:
                            report_blocks.append(f"  Progress recorded: {note}")
                        else:
                            report_blocks.append("  A status update was recorded without an additional remark.")
                        report_blocks.append(f"  Status recorded: {entry['status']}.")
                report_blocks.append("")
            report_blocks.append("")
        if not activities:
            report_blocks.append("No task starts or recorded follow-ups for this period.")
        report_text = "\n".join(report_blocks).strip()
        st.text_area("Your detailed day-by-day report", report_text, height=360)
        st.download_button(
            "⬇️ Download detailed written report",
            report_text.encode("utf-8"),
            file_name=f"detailed_daily_report_{start.isoformat()}_to_{end.isoformat()}.txt",
            mime="text/plain",
        )
        st.caption("Only activity actually recorded in the app can appear. Older overwritten remarks cannot be reconstructed.")

st.divider()
st.caption("Personal workspace  ·  Supabase storage  ·  Export and back up your records regularly")
