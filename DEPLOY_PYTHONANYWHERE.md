# 🚀 Deploy LIFEXIA to PythonAnywhere (Free)

## Step-by-Step Guide

### 1. Create Account
Go to **[pythonanywhere.com](https://www.pythonanywhere.com)** → Sign up (free)

### 2. Open Bash Console
Dashboard → **Consoles** → Start a new **Bash** console

### 3. Clone Your Repo
```bash
git clone https://github.com/Aditya33534523/lifexia.git
cd lifexia
```

### 4. Create Virtual Environment
```bash
mkvirtualenv lifexia --python=python3.10
pip install flask flask-cors flask-session python-dotenv requests flask-sqlalchemy gunicorn bcrypt PyJWT bleach werkzeug pillow
pip install sentence-transformers chromadb langchain langchain-community langchain-huggingface
```

> ⚠️ **Skip the heavy LLM packages** (`torch`, `transformers`, `accelerate`) — the free tier doesn't have enough RAM for the 3B model. The app will use the **built-in drug database** as fallback, which works great!

### 5. Create `.env` File
```bash
cat > ~/lifexia/.env << 'EOF'
SECRET_KEY=lifexia-secret-key-2024-change-in-production
FLASK_ENV=production
WHATSAPP_ACCESS_TOKEN=YOUR_TOKEN_HERE
WHATSAPP_PHONE_NUMBER_ID=1001511003041414
WHATSAPP_VERIFY_TOKEN=1555128022409639
ADMIN_WHATSAPP_NUMBER=+916351026800
PORT=5001
EOF
```
> 🔐 Replace `YOUR_TOKEN_HERE` with your actual WhatsApp access token from `.env` on your local machine

### 6. Configure Web App
1. Go to **Web** tab → **Add a new web app**
2. Choose **Manual configuration** → **Python 3.10**
3. Set these values:

| Setting | Value |
|---------|-------|
| Source code | `/home/YOUR_USERNAME/lifexia` |
| Working directory | `/home/YOUR_USERNAME/lifexia` |
| Virtualenv | `/home/YOUR_USERNAME/.virtualenvs/lifexia` |

4. Click **WSGI configuration file** link and replace its content with:

```python
import sys
import os

project_home = '/home/YOUR_USERNAME/lifexia'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

from backend.app import app as application
```

### 7. Set Static Files
In the **Web** tab → **Static files** section:

| URL | Directory |
|-----|-----------|
| `/static` | `/home/YOUR_USERNAME/lifexia/frontend/static` |

### 8. Reload & Test
Click **Reload** button → Visit `https://YOUR_USERNAME.pythonanywhere.com`

### 9. Set WhatsApp Webhook
In [Meta Developer Console](https://developers.facebook.com/apps/) → WhatsApp → Configuration:

| Setting | Value |
|---------|-------|
| Webhook URL | `https://YOUR_USERNAME.pythonanywhere.com/api/whatsapp/webhook` |
| Verify Token | `1555128022409639` |
| Subscribe to | `messages` |

## Updating Code Later
```bash
cd ~/lifexia && git pull origin main
```
Then click **Reload** in the Web tab.

## Troubleshooting
- **Error logs**: Web tab → Log files → Error log
- **WhatsApp not working**: Check that Facebook/Meta is on [PythonAnywhere's whitelist](https://www.pythonanywhere.com/whitelist/)
- **Import errors**: Make sure virtualenv is active: `workon lifexia`
