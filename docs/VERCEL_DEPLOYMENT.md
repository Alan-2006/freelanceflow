# Vercel Deployment & Google ID Authentication Guide

This guide walks you through deploying **FreelanceFlow** on [Vercel](https://vercel.com) and configuring **Google OAuth 2.0 & Google ID Authentication**.

---

## 1. Setting Up Google ID / Google OAuth Authentication

### Step 1: Create a Google Cloud Project
1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown in the top bar and select **New Project**.
3. Name your project (e.g., `FreelanceFlow`) and click **Create**.

### Step 2: Configure the OAuth Consent Screen
1. In the left navigation, go to **APIs & Services** > **OAuth consent screen**.
2. Select **External** (available to any Google account user) and click **Create**.
3. Fill in:
   - **App name**: `FreelanceFlow`
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
4. Click **Save and Continue**.
5. On the **Scopes** page, click **Add or Remove Scopes** and select:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`
6. Click **Save and Continue** through the remaining steps.

### Step 3: Create OAuth 2.0 Web Client Credentials
1. Go to **APIs & Services** > **Credentials**.
2. Click **+ Create Credentials** > **OAuth client ID**.
3. Under **Application type**, choose **Web application**.
4. Name: `FreelanceFlow Web Client`.
5. Under **Authorized JavaScript origins**, add:
   - `http://127.0.0.1:8000`
   - `http://localhost:8000`
   - `https://<your-project-name>.vercel.app` *(add after creating Vercel app)*
6. Under **Authorized redirect URIs**, add:
   - `http://127.0.0.1:8000/auth/google/callback/`
   - `http://localhost:8000/auth/google/callback/`
   - `https://<your-project-name>.vercel.app/auth/google/callback/`
7. Click **Create**.
8. Copy the generated **Client ID** and **Client Secret**.

### Step 4: Add to Local `.env`
Add the following to your local `d:\ff\pyhtonpro\.env`:
```env
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-google-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://127.0.0.1:8000/auth/google/callback/
```

---

## 2. Deploying to Vercel

FreelanceFlow is pre-configured for Vercel with:
- `vercel.json` (Serverless Python runtime with WSGI routing)
- `api/index.py` (Serverless WSGI application handler)
- `build_files.sh` (Automated static files collection)
- `whitenoise` (Production static asset streaming with gzip/brotli compression)
- `config/settings/prod.py` (Production security & database fallback)

### Option A: Deploy via GitHub (Recommended)
1. Push your code to GitHub:
   ```bash
   git init
   git add .
   git commit -m "feat: FreelanceFlow with Vercel and Google Auth"
   git branch -M main
   git remote add origin https://github.com/<your-username>/freelanceflow.git
   git push -u origin main
   ```
2. Go to [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New** > **Project**.
3. Select your GitHub repository.
4. Set the **Framework Preset** to **Other**.
5. In **Environment Variables**, add the variables listed below in Section 3.
6. Click **Deploy**.

---

### Option B: Deploy via Vercel CLI
```bash
# 1. Install Vercel CLI globally if not already installed
npm i -g vercel

# 2. Log in and deploy
vercel

# 3. For production release:
vercel --prod
```

---

## 3. Production Environment Variables for Vercel

Set these in your **Vercel Project Settings > Environment Variables**:

| Variable | Description | Example / Recommended Value |
| :--- | :--- | :--- |
| `DJANGO_SETTINGS_MODULE` | Active settings module | `config.settings.prod` |
| `SECRET_KEY` | Production encryption key | *(Generate a 50-character random string)* |
| `DEBUG` | Debug flag | `False` |
| `ALLOWED_HOSTS` | Whitelisted host headers | `*` or `.vercel.app` |
| `DATABASE_URL` | Production PostgreSQL connection string | `postgresql://user:pass@ep-cool-db.us-east-1.aws.neon.tech/neondb?sslmode=require` *(e.g. Free Neon or Supabase)* |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | `xxxxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | `GOCSPX-xxxxx` |
| `GOOGLE_OAUTH_REDIRECT_URI` | Google OAuth callback URL | `https://<your-project-name>.vercel.app/auth/google/callback/` |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF | `https://*.vercel.app` |

> **Pro-Tip for Production Database:**
> Serverless platforms like Vercel have ephemeral disk filesystems. For production, connect a free hosted PostgreSQL database such as [Neon.tech](https://neon.tech) or [Supabase](https://supabase.com) by pasting the connection string into the `DATABASE_URL` variable.
