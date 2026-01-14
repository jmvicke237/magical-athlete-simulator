# Deploying Magical Athlete Simulator to Streamlit Community Cloud

## Quick Deployment Steps

### 1. Prerequisites
- Your GitHub repository is already set up ✓
- You have a GitHub account

### 2. Deploy to Streamlit Community Cloud (FREE)

1. **Go to [share.streamlit.io](https://share.streamlit.io)**

2. **Sign in with your GitHub account**

3. **Click "New app"**

4. **Fill in the deployment form:**
   - **Repository:** `jmvicke237/magical-athlete-simulator` (or your repo path)
   - **Branch:** `main`
   - **Main file path:** `app.py`

5. **Click "Deploy!"**

That's it! Streamlit will:
- Install dependencies from `requirements.txt`
- Start your app
- Give you a public URL like: `https://your-app-name.streamlit.app`

### 3. Share with Your Team

Once deployed, you'll get a URL like:
```
https://magical-athlete-simulator.streamlit.app
```

Share this URL with your team - they can access it from any browser, no setup needed!

## Features

✓ **Free hosting** (no credit card required)
✓ **Auto-deploys** when you push to GitHub
✓ **HTTPS** included
✓ **No server management** needed

## Updating the App

Any time you push changes to the `main` branch on GitHub, Streamlit Community Cloud will automatically redeploy your app with the latest changes.

## Alternative: Run Locally

If team members want to run locally instead:

```bash
git clone https://github.com/jmvicke237/magical-athlete-simulator.git
cd magical-athlete-simulator
pip install -r requirements.txt
streamlit run app.py
```

Then visit `http://localhost:8501` in their browser.

## Troubleshooting

**App won't deploy?**
- Check that `requirements.txt` lists all dependencies
- Make sure `app.py` is in the root directory
- Check deployment logs in Streamlit Community Cloud dashboard

**App is slow?**
- Free tier has resource limits
- Consider optimizing simulation count or caching results

**Need more control?**
- Can upgrade to Streamlit Community Cloud paid tier
- Or deploy to Heroku, AWS, Google Cloud, etc.
