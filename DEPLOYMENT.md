# Railway Deployment Guide

## Prerequisites
1. Railway account (https://railway.app)
2. GitHub account
3. Your Telegram bot token from @BotFather
4. Groq API key from https://console.groq.com

## Deployment Steps

### 1. Prepare Your Repository
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Deploy to Railway
1. Go to https://railway.app
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically detect it's a Python project

### 3. Configure Environment Variables
In Railway dashboard, go to Variables tab and add:
- `BOT_TOKEN`: Your Telegram bot token
- `GROQ_API_KEY`: Your Groq API key

### 4. Deploy
Railway will automatically build and deploy your bot.

## Important Notes
- The bot will run 24/7 on Railway
- Generated files are stored temporarily (Railway has ephemeral storage)
- Logs are available in Railway dashboard
- The bot will automatically restart if it crashes

## Monitoring
- Check Railway dashboard for logs and metrics
- Bot status can be monitored through Telegram
- Use `/start` command to test if bot is responsive

## Troubleshooting
- Check Railway logs for errors
- Ensure environment variables are set correctly
- Verify bot token is valid with @BotFather
- Test Groq API key separately if needed