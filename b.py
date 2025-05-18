#!/usr/bin/env python3
import requests
import time
import hashlib

# ─── Configuration Defaults ─────────────────────────────────────────────────────
LOGIN_URL       = "https://www.bounty-news.com/api/member/login"
PAGE_URL        = "https://www.bounty-news.com/api/worksInfo/page"
CONTENT_URL     = "https://www.bounty-news.com/api/worksInfoContent/getContent"
START_READ_URL  = "https://www.bounty-news.com/api/worksInfo/startRead"
CLAIM_URL       = "https://www.bounty-news.com/api/worksInfo/claimReward"
DAILY_INFO_URL  = "https://www.bounty-news.com/api/memberReadingReward/info"
DAILY_AWARD_URL = "https://www.bounty-news.com/api/memberReadingReward/getAward"

SALES_PERSON_ID = "232"
LANGUAGE        = "en_US"
USER_SYSTEM     = "android 11"
USER_DEVICE     = "firefox/128.0"

CATEGORY_ID     = "1921117247997878274"
PAGE_SIZE       = 10
MAX_PAGES       = 3
DELAY_SECONDS   = 32
MAX_READS       = 20

# ─── Credentials (phone + code) ────────────────────────────────────────────────
credentials = [
    {"phone": "09582811870", "code": "755"},
    {"phone": "09291078442", "code": "586"},
    {"phone": "09497941608", "code": "964"},
    {"phone": "09344474585", "code": "922"},
    {"phone": "09465307245", "code": "715"},
    # Add more if needed
]

# ─── Session Setup ──────────────────────────────────────────────────────────────
def setup_session():
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "language": LANGUAGE,
        "X-User-System": USER_SYSTEM,
        "X-User-Device-Type": USER_DEVICE,
        "User-Agent": "Mozilla/5.0 Firefox/128.0"
    })
    return session

# ─── Core Functions ──────────────────────────────────────────────────────────────

def login(session, phone, code):
    raw = f"password{code}"
    pw_hash = hashlib.md5(raw.encode()).hexdigest()
    payload = {"phone": phone, "password": pw_hash}
    resp = session.post(LOGIN_URL, json=payload)
    data = resp.json()
    if resp.status_code != 200 or not data.get("success"):
        raise RuntimeError(f"Login failed: {data.get('message') or resp.text}")
    token = data["result"]["token"]
    head = data["result"]["tokenHead"]
    auth = f"{head} {token}"
    session.headers.update({
        "Authorization": auth,
        "memberInfoId": str(data["result"]["sysUserId"]),
        "salesPersonId": SALES_PERSON_ID
    })
    print(f"[{phone}] ✔ Logged in")

def fetch_page(session, page_no):
    resp = session.post(PAGE_URL, json={"pageNo": page_no, "pageSize": PAGE_SIZE, "categoryId": CATEGORY_ID})
    js = resp.json()
    if not js.get("success"):
        raise RuntimeError("Failed to fetch page")
    return js["result"]["list"]

def fetch_content_id(session, works_info_id):
    resp = session.post(CONTENT_URL, json={"id": works_info_id})
    js = resp.json()
    if not js.get("success") or not js.get("result"):
        return None
    return js["result"][0]["id"]

def process_item(session, info_id, phone):
    content_id = fetch_content_id(session, info_id)
    if not content_id:
        print(f"[{phone}] ⚠️ No content for article {info_id}")
        return False
    resp = session.post(START_READ_URL, json={"worksInfoContentId": content_id, "worksInfoId": info_id})
    js = resp.json()
    if js.get("success") is False and js.get("businessMessage") == "AlreadyRead":
        print(f"[{phone}] ⏭️ Article {info_id} already read, skipping")
        return False
    print(f"[{phone}] 📖 Reading article {info_id}...")
    time.sleep(DELAY_SECONDS)
    claim_resp = session.post(CLAIM_URL, json={"worksInfoContentId": content_id}).json()
    if claim_resp.get("success"):
        print(f"[{phone}] 🎉 Claimed article {info_id}")
        return True
    else:
        print(f"[{phone}] ❌ Claim failed for article {info_id}")
        return False

def claim_daily_rewards(session, phone):
    resp = session.post(DAILY_INFO_URL, json={})
    data = resp.json()
    if not data.get("success") or "result" not in data:
        print(f"[{phone}] ⚠️ Could not retrieve daily reading rewards info")
        return
    tiers = data["result"].get("memberReadingRewardDetailVoList", [])
    print(f"[{phone}] 🔄 Checking daily reward tiers...")
    for tier in tiers:
        status = tier.get("memberReadingRewardStatus")
        num = tier.get("workInfoReadingNum")
        if status == "complete":
            print(f"[{phone}] Claiming daily tier reward for reading {num} articles...")
            claim_resp = session.post(DAILY_AWARD_URL, json={"workInfoReadingNum": num}).json()
            if claim_resp.get("success"):
                print(f"[{phone}] 🎁 Successfully claimed tier reward for {num} articles")
            else:
                print(f"[{phone}] ⚠️ Failed to claim tier reward for {num} articles")
        else:
            print(f"[{phone}] Tier reward for {num} articles not completed yet")

def run_for_user(cred):
    phone = cred["phone"]
    code = cred["code"]
    session = setup_session()
    try:
        login(session, phone, code)
        reads = 0
        for page in range(1, MAX_PAGES + 1):
            items = fetch_page(session, page)
            for itm in items:
                if reads >= MAX_READS:
                    break
                if process_item(session, itm["id"], phone):
                    reads += 1
            if reads >= MAX_READS:
                break
        claim_daily_rewards(session, phone)
        print(f"[{phone}] ✅ Done. Articles read: {reads}\n")
    except Exception as e:
        print(f"[{phone}] 🚨 Error: {e}\n")

if __name__ == "__main__":
    print("🌟 Starting Bounty News Auto Claimer...\n")
    for c in credentials:
        print(f"▶️ Processing {c['phone']}")
        run_for_user(c)
    print("🏁 All tasks completed.")