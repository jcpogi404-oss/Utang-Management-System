# 🚀 DEPLOY YOUR UTANG APP TO RENDER (FREE HOSTING WITH HTTPS)

## STEP 1: CREATE GITHUB ACCOUNT & REPOSITORY

1. Go to https://github.com
2. Click "Sign up" (if you don't have an account)
3. Click the "+" icon (top right) → "New repository"
4. Repository name: `utang-app`
5. Make it **Public**
6. Click "Create repository"

---

## STEP 2: PUSH YOUR CODE TO GITHUB

Open your terminal and run these commands:

```bash
cd /home/jayxi/Videos/Utang

# Initialize git (if not already done)
git init

# Configure git (replace with your info)
git config user.name "Your Name"
git config user.email "your-email@example.com"

# Add all files
git add .

# Commit
git commit -m "Initial commit - Utang Record System"

# Connect to GitHub (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/utang-app.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Note:** You'll be asked for your GitHub username and password (use Personal Access Token instead of password)

### To create a Personal Access Token:
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → Select "repo" scope
3. Copy the token and use it as password when pushing

---

## STEP 3: DEPLOY TO RENDER

1. Go to https://render.com
2. Click "Get Started" or "Sign Up"
3. Sign up with GitHub (easiest)
4. Click "New +" → "Web Service"
5. Click "Connect" next to your `utang-app` repository
6. Fill in the details:
   - **Name:** `utang-app` (or any name you want)
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app_sqlite:app`
   - **Instance Type:** Free
7. Click "Create Web Service"

---

## STEP 4: WAIT FOR DEPLOYMENT (5-10 minutes)

Render will:
- Install dependencies
- Start your app
- Give you a FREE HTTPS URL like: `https://utang-app-xxxx.onrender.com`

---

## STEP 5: TEST YOUR APP

1. Once deployment is complete, click your app URL
2. Your app should load with HTTPS! ✅

---

## STEP 6: CREATE ANDROID APK

1. Go to https://www.pwabuilder.com/
2. Enter your Render URL: `https://utang-app-xxxx.onrender.com`
3. Click "Start"
4. Click "Package For Stores"
5. Click "Android" → "Generate"
6. Download your APK file
7. Transfer to your Android phone and install!

---

## IMPORTANT NOTES:

⚠️ **Free Render apps sleep after 15 minutes of inactivity**
- First load after sleep takes ~30 seconds to wake up
- Keep active with a cron job or upgrade to paid plan ($7/month)

⚠️ **Database persistence:**
- Free tier may reset database on redeploy
- For production, consider upgrading or using external database

⚠️ **Local development:**
- Your local version at `192.168.6.78:5000` still works!
- Changes need to be pushed to GitHub to update Render

---

## TROUBLESHOOTING:

**If deployment fails:**
1. Check logs in Render dashboard
2. Make sure all files are pushed to GitHub
3. Verify requirements.txt has all dependencies

**Need help?** Check the deployment logs in Render dashboard for error messages.

---

## NEXT STEPS AFTER DEPLOYMENT:

1. Test all features on the live URL
2. Generate APK using PWABuilder
3. Install APK on your Android phone
4. Share the URL with others if needed!

🎉 **Your app will be live at:** `https://your-app-name.onrender.com`
