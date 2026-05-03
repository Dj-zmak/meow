import os, asyncio, requests
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()

# গ্লোবাল ডাটা স্টোর
bot_logs = []
user_config = {"email": "", "password": "", "active": False}

def claim_honeygain():
    if not user_config["active"]: return
    
    email = user_config["email"]
    password = user_config["password"]
    now = datetime.now().strftime("%H:%M:%S")
    
    try:
        # Login
        url = "https://dashboard.honeygain.com/api/v1/users/tokens"
        res = requests.post(url, json={"email": email, "password": password})
        
        if res.status_code == 200:
            token = res.json()['data']['access_token']
            # Claim
            claim_url = "https://dashboard.honeygain.com/api/v1/contest_winnings"
            headers = {"Authorization": f"Bearer {token}"}
            claim_res = requests.post(claim_url, headers=headers)
            
            if claim_res.status_code == 200:
                msg = f"[{now}] ✅ Success: Pot Claimed!"
            else:
                msg = f"[{now}] ⚠️ Info: Already claimed or not ready."
        else:
            msg = f"[{now}] ❌ Error: Login Failed."
            
    except Exception as e:
        msg = f"[{now}] ⚠️ Error: {str(e)}"
    
    bot_logs.append(msg)
    if len(bot_logs) > 15: bot_logs.pop(0)

# ৩ ঘণ্টা পর পর অটো রান হওয়ার শিডিউলার
scheduler = BackgroundScheduler()
scheduler.add_job(claim_honeygain, 'interval', hours=3)
scheduler.start()

@app.get("/", response_class=HTMLResponse)
async def home():
    # সরাসরি HTML ফাইলটি রিটার্ন করবে (নিচে দেওয়া হলো)
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/start")
async def start_bot(email: str = Form(...), password: str = Form(...)):
    user_config["email"] = email
    user_config["password"] = password
    user_config["active"] = True
    claim_honeygain() # স্টার্ট করার সাথে সাথে একবার ক্লেইম করবে
    return {"status": "Bot Started"}

@app.get("/logs")
async def get_logs():
    return {"logs": bot_logs, "active": user_config["active"]}
