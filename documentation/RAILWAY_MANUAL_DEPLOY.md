# Railway Manual Deployment - Step by Step

## Step-by-Step Instructions

### Step 1: Go to Railway
1. Open your browser
2. Go to: **https://railway.app**
3. Click **"Start a New Project"** or **"Login"** if you have an account

### Step 2: Sign In
1. Click **"Login with GitHub"**
2. Authorize Railway to access your GitHub account
3. You'll be redirected back to Railway dashboard

### Step 3: Create New Project
1. Click **"+ New Project"** button (usually top right)
2. Select **"Deploy from GitHub repo"**
3. If prompted, authorize Railway to access your GitHub repos

### Step 4: Find PolySniffer Repo
1. In the repo search box, type: **`oliver-oliver/PolySniffer`**
2. If the repo exists, click on it
3. If it doesn't exist, we can use an alternative (see below)

### Step 5: Deploy
1. Railway will automatically detect the project type
2. Click **"Deploy"** or it may auto-deploy
3. Wait 2-5 minutes for deployment to complete

### Step 6: Get Your URL
1. Once deployed, Railway will show you a **public URL**
2. It will look like: `https://your-app-name.railway.app`
3. **Copy this URL** - we'll need it!

## Alternative: If PolySniffer Repo Doesn't Exist

If the GitHub repo `oliver-oliver/PolySniffer` doesn't exist or is private, we have alternatives:

### Option A: Use Chrome DevTools (Easiest - No Setup!)
1. Open Chrome
2. Press **F12** to open DevTools
3. Go to **Network** tab
4. Navigate to: `https://oliverenterprises.app.saasify.cloud/scp/login.php`
5. Login with your credentials
6. Right-click in the Network tab → **"Save all as HAR"**
7. This gives us the same data as PolySniffer!

### Option B: Use Playwright Script (Already in Codebase)
We already have a Playwright-based login script that can capture browser behavior:
- File: `dose/services/osticket_playwright_login.py`
- This can be used to debug the login flow

### Option C: Check if PolySniffer is Public
Try accessing the repo directly:
- https://github.com/oliver-oliver/PolySniffer

If it's private, you may need to:
- Fork it to your account
- Make it public temporarily
- Or use one of the alternatives above

## What to Do After Deployment

Once you have your Railway URL (or if using DevTools):

1. **Test it works**: Open the URL in browser
2. **Enter OS ticket URL**: `https://oliverenterprises.app.saasify.cloud/scp/login.php`
3. **Login and navigate**
4. **Export/capture** the requests
5. **Compare** with our proxy output

## Quick Test

To test if Railway deployment worked:
1. Open your Railway URL
2. You should see the PolySniffer interface
3. Enter any URL to test (e.g., `https://example.com`)
4. If it loads, it's working! ✅

