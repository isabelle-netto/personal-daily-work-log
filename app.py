from datetime import date, datetime, timedelta
import hmac
import time
import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Daily Work Log | Personal Workspace", page_icon="📋", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
:root { color-scheme: light; }
[data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: #F6F8FC; color: #182B49; }
[data-testid="stSidebar"] { background: #FFFFFF; }
.block-container { max-width: 1180px; padding-top: 2.6rem; padding-bottom: 4rem; }
h1, h2, h3 { color: #122D4B !important; letter-spacing: -.028em; }
h1 { font-weight: 750 !important; }
p, label, .stMarkdown { color: #33465F; }
[data-testid="stMetric"] { background: white; border: 1px solid #E5EAF2; border-radius: 14px; padding: 18px 20px; box-shadow: 0 3px 14px rgba(13,40,73,.035); }
[data-testid="stMetricLabel"] { color: #60738C; }
[data-testid="stMetricValue"] { color: #173B62; }
[data-testid="stForm"], [data-testid="stExpander"], [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; }
.stButton button[kind="primary"], .stDownloadButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] { background: #174A7E !important; border-color: #174A7E !important; color: white !important; border-radius: 9px; }
.stButton button, .stDownloadButton button { border-radius: 9px; }
[data-baseweb="tab-list"] { gap: 14px; background: transparent; border-bottom: 1px solid #E1E8F0; }
[data-baseweb="tab"] { font-weight: 600; }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
</style>""", unsafe_allow_html=True)

def login_gate():
    # CRITICAL: call this before accessing Supabase or showing work records.
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

    st.markdown("### Your personal workspace")
    st.caption("DAILY WORK LOG  /  PRIVATE ACCESS")
    st.title("Welcome back")
    st.write("Sign in to view your tasks, daily progress and reports.")
    lock_until = st.session_state.get("worklog_lock_until", 0)
    if time.time() < lock_until:
        st.warning("Too many attempts. Please try again in a few minutes.")
        st.stop()
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

def update_task(task_id, task_date, task, status, remark):
    get_supabase().table("work_tasks").update({"task_date": task_date.isoformat(), "task": task.strip(), "status": status, "remark": remark.strip()}).eq("id", int(task_id)).execute()

def delete_task(task_id):
    get_supabase().table("work_tasks").delete().eq("id", int(task_id)).execute()

def read_tasks():
    # Supabase API returns up to 1,000 rows per request by default; paginate all records.
    rows = []
    offset = 0
    while True:
        batch = (get_supabase().table("work_tasks")
                 .select("id,task_date,task,status,remark,created_at,updated_at")
                 .order("task_date", desc=True).order("id", desc=True)
                 .range(offset, offset + 999).execute().data or [])
        rows.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return pd.DataFrame(rows, columns=["id", "task_date", "task", "status", "remark", "created_at", "updated_at"])

st.caption('PERSONAL WORKSPACE  /  PRODUCTIVITY & REPORTING')
st.title('Daily Work Log')
st.write('Plan your day, follow up unfinished work across dates, and build clear reports — all in one place.')

try:
    all_tasks = read_tasks()
except Exception as exc:
    st.error("Could not connect to Supabase. Check your Streamlit secrets and database setup.")
    st.caption("Check the Supabase URL/key and the SQL privileges on public.work_tasks. Detailed server errors are hidden to protect credentials.")
    st.stop()
today_iso = date.today().isoformat()
today_tasks = all_tasks[all_tasks['task_date'] == today_iso]
today_total = len(today_tasks)
today_completed = int((today_tasks['status'] == 'Completed').sum())
today_pending = int((today_tasks['status'] == 'Pending').sum())
today_unfinished = int((today_tasks['status'] == 'Not Completed').sum())
pending_all = all_tasks[all_tasks['status'] == 'Pending'].copy()
st.caption(f"TODAY  ·  {date.today().strftime('%A, %d %B %Y')}")
k1, k2, k3, k4 = st.columns(4)
k1.metric('Tasks today', today_total)
k2.metric('Completed', today_completed)
k3.metric('Open pending (all dates)', len(pending_all))
k4.metric('Not completed', today_unfinished)
st.write('')
tab_pending, tab_add, tab_update, tab_report = st.tabs(['⏳  Pending tasks', '＋  Add tasks', '✓  Daily review', '▤  Reports & history'])

with tab_pending:
    st.subheader('Your open tasks')
    st.write('Every unfinished task stays here, **regardless of when you added it**. Update it whenever you make progress; it will disappear from this list only when you change its status.')
    left, right = st.columns([3, 1])
    with left:
        pending_search = st.text_input('Find an open task', placeholder='Search by task or remark...', key='pending_search')
    with right:
        pending_order = st.selectbox('Sort by', ['Oldest first', 'Newest first'], key='pending_order')
    pending_view = pending_all.copy()
    if pending_search.strip():
        q = pending_search.strip()
        pending_view = pending_view[
            pending_view['task'].str.contains(q, case=False, regex=False, na=False) |
            pending_view['remark'].fillna('').str.contains(q, case=False, regex=False, na=False)
        ]
    pending_view = pending_view.sort_values(['task_date', 'id'], ascending=(pending_order == 'Oldest first'))
    st.caption(f'{len(pending_view)} open task(s) shown · {len(pending_all)} open in total')
    if pending_view.empty:
        st.success('No pending tasks found. You are all caught up!' if pending_all.empty else 'No tasks match that search.')
    else:
        for item in pending_view.itertuples(index=False):
            original_date = date.fromisoformat(item.task_date)
            days_old = (date.today() - original_date).days
            age = (f'{days_old} day(s) old' if days_old > 0 else 'Added today' if days_old == 0 else 'Upcoming')
            with st.container(border=True):
                st.markdown(f'**{item.task}**')
                st.caption(f'Originally planned: {original_date.strftime("%d %b %Y")}  ·  {age}')
                if isinstance(item.remark, str) and item.remark.strip():
                    st.markdown(f'**Latest remark:** {item.remark}')
                with st.form(f'pending_form_{item.id}'):
                    new_status = st.selectbox('Update status', STATUSES, key=f'pending_status_{item.id}')
                    new_remark = st.text_area('Progress note / remark (optional)', value=item.remark or '', key=f'pending_remark_{item.id}', height=85, placeholder='e.g. Followed up today; still awaiting approval')
                    save_pending = st.form_submit_button('Save progress', type='primary')
                    if save_pending:
                        try:
                            update_task(item.id, original_date, item.task, new_status, new_remark)
                            st.rerun()
                        except Exception:
                            st.error('Could not save your update. Please try again.')
                st.caption('Tip: Keep the status Pending and save a new remark to record progress; select Completed to close it.')

with tab_add:
    st.subheader('Add a task or goal')
    st.write('You can enter several tasks for the same day. New entries start as **Pending**.')
    with st.form('new_task_form', clear_on_submit=True):
        task_date = st.date_input('Date', value=date.today(), format='DD/MM/YYYY')
        task = st.text_area('Task / goal for the day', placeholder='e.g. Prepare the stakeholder outreach report', height=100)
        submitted = st.form_submit_button('Save task', type='primary')
        if submitted:
            if not task.strip():
                st.error('Please type a task before saving.')
            else:
                add_task(task_date, task)
                st.success('Task saved.')
                st.rerun()
    st.info('Tip: Enter each task separately so you can mark individual tasks as completed or not completed.')

with tab_update:
    st.subheader('Review your day')
    day = st.date_input('Choose the date to update', value=date.today(), format='DD/MM/YYYY', key='update_day')
    day_tasks = all_tasks[all_tasks['task_date'] == day.isoformat()]
    if day_tasks.empty:
        st.info('No tasks found for this date. Add one in the first tab.')
    else:
        st.caption(f'{len(day_tasks)} task(s) on {day.strftime("%d %B %Y")}')
        for item in day_tasks.itertuples(index=False):
            with st.expander(f'{item.status}  |  {item.task[:110]}', expanded=(item.status == 'Pending')):
                with st.form(f'edit_task_{item.id}'):
                    new_date = st.date_input('Date', value=date.fromisoformat(item.task_date), format='DD/MM/YYYY', key=f'date_{item.id}')
                    new_task = st.text_area('Task / goal', value=item.task, key=f'task_{item.id}')
                    status = st.selectbox('End-of-day outcome', STATUSES, index=STATUSES.index(item.status), key=f'status_{item.id}')
                    remark = st.text_area('Remark (optional)', value=item.remark, placeholder='e.g. Completed and sent to manager; or postponed awaiting approval.', key=f'remark_{item.id}')
                    save = st.form_submit_button('Save update', type='primary')
                    if save:
                        if not new_task.strip():
                            st.error('The task description cannot be empty.')
                        else:
                            update_task(item.id, new_date, new_task, status, remark)
                            st.success('Update saved.')
                            st.rerun()
                with st.popover('Delete this task'):
                    st.warning('This deletion cannot be undone.')
                    if st.button('Confirm delete', key=f'delete_{item.id}'):
                        delete_task(item.id)
                        st.rerun()

with tab_report:
    st.subheader('Work report & history')
    today = date.today()
    default_start = today.replace(day=1)
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 2])
        with c1:
            start = st.date_input('From date', value=default_start, format='DD/MM/YYYY', key='filter_start')
        with c2:
            end = st.date_input('To date', value=today, format='DD/MM/YYYY', key='filter_end')
        with c3:
            selected_statuses = st.multiselect('Task status', STATUSES, default=STATUSES)
        search = st.text_input('Search tasks or remarks', placeholder='Search by keyword…')

    if start > end:
        st.error('The From date must be on or before the To date.')
    else:
        filtered = all_tasks[
            (all_tasks['task_date'] >= start.isoformat()) &
            (all_tasks['task_date'] <= end.isoformat()) &
            (all_tasks['status'].isin(selected_statuses))
        ].copy()
        if search.strip():
            filtered = filtered[
                filtered['task'].str.contains(search.strip(), case=False, regex=False, na=False) |
                filtered['remark'].str.contains(search.strip(), case=False, regex=False, na=False)
            ]

        counts = filtered['status'].value_counts()
        total = len(filtered)
        completed = int(counts.get('Completed', 0))
        pending = int(counts.get('Pending', 0))
        not_completed = int(counts.get('Not Completed', 0))
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric('Total tasks', total)
        k2.metric('Completed', completed)
        k3.metric('Not completed', not_completed)
        k4.metric('Pending', pending)
        k5.metric('Completion rate', f'{completed / total:.0%}' if total else '—')
        st.caption('Completion rate = completed tasks divided by all tasks matching the filters, including pending tasks.')

        if filtered.empty:
            st.info('There are no tasks matching these filters.')
        else:
            display = filtered[['task_date', 'task', 'status', 'remark']].rename(columns={
                'task_date': 'Date', 'task': 'Task / Goal', 'status': 'Outcome', 'remark': 'Remark'
            })
            display['Date'] = pd.to_datetime(display['Date']).dt.strftime('%d/%m/%Y')
            st.dataframe(display, use_container_width=True, hide_index=True)

            csv = display.to_csv(index=False).encode('utf-8-sig')
            st.download_button('⬇️ Download filtered CSV report', data=csv,
                               file_name=f'work_log_{start.isoformat()}_to_{end.isoformat()}.csv',
                               mime='text/csv', type='primary')

            st.markdown('#### Daily report (easy to copy)')
            blocks = []
            for day_string, group in filtered.sort_values(['task_date', 'id']).groupby('task_date', sort=False):
                blocks.append(date.fromisoformat(day_string).strftime('%A, %d %B %Y'))
                for _, row in group.iterrows():
                    line = f"- {row['task']} — {row['status']}"
                    if row['remark'].strip():
                        line += f" | Remark: {row['remark']}"
                    blocks.append(line)
                blocks.append('')
            report_text = '\n'.join(blocks).strip()
            st.text_area('Copy this into your work report', report_text, height=240)
            st.download_button('⬇️ Download text report', report_text.encode('utf-8'),
                               file_name=f'work_report_{start.isoformat()}_to_{end.isoformat()}.txt',
                               mime='text/plain')

st.divider()
st.caption("Personal workspace  ·  Supabase storage  ·  Export and back up your records regularly")
