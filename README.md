# Daily Work Log – Personal Online Edition

An online Streamlit work journal backed by your own Supabase project.

## 1. Supabase
1. Create a project under your **personal** Supabase account.
2. Open **SQL Editor > New query**; paste and run `supabase_setup.sql`.
3. From **Project Settings / Connect**, copy the **Project URL**. From **API Keys**, copy the **secret key** (`sb_secret_...`) or legacy `service_role` key. Never use the public/anon key in this app, never paste a secret key in GitHub or chat.

## 2. GitHub
1. Create a **private** repository in your personal GitHub (e.g., `personal-daily-work-log`).
2. Upload `app.py`, `requirements.txt`, `supabase_setup.sql`, `.gitignore` and this README to the repository root.
3. Do **not** upload `.streamlit/secrets.toml`, any keys, or any company confidential material.

## 3. Streamlit Community Cloud
1. Visit https://share.streamlit.io using your personal Streamlit account (connect personal GitHub).
2. Select **Create app**, choose the private repository, branch `main`, entrypoint `app.py`.
3. Under **Advanced settings > Secrets**, paste (replacing placeholders):

```toml
SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
SUPABASE_SECRET_KEY = "YOUR-SECRET-KEY"
```

4. Deploy. Keep the app **private** under **Settings > Sharing** (only specific people can view). Streamlit Community Cloud currently allows one private app on the free plan; check account availability.
5. Open your deployed `*.streamlit.app` URL from any laptop and sign in as the allowed viewer.

## 4. What you can do
- Add several dated tasks (initially Pending).
- Update completion statuses and optional remarks, or edit/delete entries.
- Filter historical reports by date, status and keyword.
- Download CSV or text report.

## Privacy
This is a single-owner app. Streamlit's **private app access control** is the login gate; there is no separate password login in the app. Do not change the Streamlit app to public, because the server uses a highly privileged Supabase key. The SQL table has Row Level Security enabled with no client policies; server secret key bypasses it.

The Supabase key must be stored **only** in Streamlit Secrets, not GitHub. Protect your personal login and enable MFA. Check your employer's data handling rules before copying confidential work content into personal services. Export/backup records regularly.

## Local test (optional)
Create `.streamlit/secrets.toml` locally with the same two secrets, run `pip install -r requirements.txt` then `streamlit run app.py`.
