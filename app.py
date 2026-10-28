from datetime import date
import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Daily Work Log", page_icon="📋", layout="wide")
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

st.title('📋 Daily Work Log')
st.caption('Plan your day • Record the outcome • Build a reliable work report')

try:
    all_tasks = read_tasks()
except Exception as exc:
    st.error("Could not connect to Supabase. Check your Streamlit secrets and database setup.")
    st.exception(exc)
    st.stop()
tab_add, tab_update, tab_report = st.tabs(['➕ Add tasks', '✅ End-of-day update', '📊 Work report & history'])

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
st.caption("Private work log • Stored in your personal Supabase project • Export records regularly")
