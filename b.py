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
    {"phone": "09137520214", "code": "872"},
    {"phone": "09170363921", "code": "521"},
    {"phone": "09258785549", "code": "835"},
    {"phone": "09554072913", "code": "602"},
    {"phone": "09220359954", "code": "609"},
    {"phone": "09489110740", "code": "638"},
    {"phone": "09194589054", "code": "254"},
    {"phone": "09137666532", "code": "993"},
    {"phone": "09248750308", "code": "298"},
    {"phone": "09506615700", "code": "399"},
    {"phone": "09362605643", "code": "794"},
    {"phone": "09494997709", "code": "700"},
    {"phone": "09546494096", "code": "767"},
    {"phone": "09154011245", "code": "395"},
    {"phone": "09200451732", "code": "729"},
    {"phone": "09470493591", "code": "820"},
    {"phone": "09267209118", "code": "825"},
    {"phone": "09363840678", "code": "877"},
    {"phone": "09523781152", "code": "395"},
    {"phone": "09457865133", "code": "855"},
    {"phone": "09217197100", "code": "443"},
    {"phone": "09103198637", "code": "473"},
    {"phone": "09276897178", "code": "408"},
    {"phone": "09475319134", "code": "376"},
    {"phone": "09404418585", "code": "162"},
    {"phone": "09325562525", "code": "258"},
    {"phone": "09208981743", "code": "344"},
    {"phone": "09507874412", "code": "726"},
    {"phone": "09341058232", "code": "868"},
    {"phone": "09381108034", "code": "801"},
    {"phone": "09498165386", "code": "654"},
    {"phone": "09311290235", "code": "297"},
    {"phone": "09175596662", "code": "638"},
    {"phone": "09270872633", "code": "411"},
    {"phone": "09278534509", "code": "791"},
    {"phone": "09568868916", "code": "965"},
    {"phone": "09456985513", "code": "644"},
    {"phone": "09343432491", "code": "293"},
    {"phone": "09517723306", "code": "504"},
    {"phone": "09176891014", "code": "501"},
    {"phone": "09202974667", "code": "336"},
    {"phone": "09177568570", "code": "242"},
    {"phone": "09198389703", "code": "673"},
    {"phone": "09210478623", "code": "354"},
    {"phone": "09497128182", "code": "351"},
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
    # compute MD5 hash of the raw password string
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
        "memberInfoId": data["result"]["sysUserId"],
        "salesPersonId": SALES_PERSON_ID
    })
    print(f"✔ Logged in: {phone}")


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


def process_item(session, info_id):
    content_id = fetch_content_id(session, info_id)
    if not content_id:
        print(f"⚠️ No content for {info_id}")
        return False
    session.post(START_READ_URL, json={"worksInfoContentId": content_id, "worksInfoId": info_id})
    print(f"📖 Reading {info_id}...")
    time.sleep(DELAY_SECONDS)
    res = session.post(CLAIM_URL, json={"worksInfoContentId": content_id}).json()
    if res.get("success"):
        print(f"🎉 Claimed {content_id}")
        return True
    else:
        print(f"❌ Claim failed {content_id}")
        return False


def claim_daily_rewards(session):
    resp = session.post(DAILY_INFO_URL, json={}).json()
    if not resp.get("success"):
        print("❌ Daily info failed")
        return
    for tier in resp["result"]["memberReadingRewardDetailVoList"]:
        if tier.get("memberReadingRewardStatus") == "complete":
            num = tier.get("workInfoReadingNum")
            res = session.post(DAILY_AWARD_URL, json={"workInfoReadingNum": num}).json()
            print(f"🎁 Daily bonus {num} claimed" if res.get("success") else f"⚠️ Daily {num} failed")


def run_for_user(cred):
    session = setup_session()
    try:
        login(session, cred["phone"], cred["code"])
        reads = 0
        for page in range(1, MAX_PAGES+1):
            items = fetch_page(session, page)
            for itm in items:
                if reads >= MAX_READS:
                    break
                if process_item(session, itm["id"]): reads += 1
            if reads >= MAX_READS:
                break
        print("🔄 Claiming daily rewards...")
        claim_daily_rewards(session)
        print(f"✅ Done for {cred['phone']} ({reads} reads)\n")
    except Exception as e:
        print(f"🚨 {cred['phone']} error: {e}\n")


if __name__ == "__main__":
    print("🌟 Starting Bounty News Auto Claimer...")
    for c in credentials:
        print(f"\n▶️ {c['phone']}")
        run_for_user(c)
    print("\n🏁 All tasks completed")
