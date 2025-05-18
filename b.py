#!/usr/bin/env python3
import requests
import time
import hashlib
import threading

# ─── Configuration Defaults ─────────────────────────────────────────────────────
LOGIN_URL           = "https://www.bounty-news.com/api/member/login"
PAGE_URL            = "https://www.bounty-news.com/api/worksInfo/page"
HISTORY_URL         = "https://www.bounty-news.com/api/worksHistory/pageHistory"
CONTENT_URL         = "https://www.bounty-news.com/api/worksInfoContent/getContent"
START_READ_URL      = "https://www.bounty-news.com/api/worksInfo/startRead"
CLAIM_URL           = "https://www.bounty-news.com/api/worksInfo/claimReward"
DAILY_INFO_URL      = "https://www.bounty-news.com/api/memberReadingReward/info"
DAILY_AWARD_URL     = "https://www.bounty-news.com/api/memberReadingReward/getAward"

SALES_PERSON_ID = "232"
LANGUAGE        = "en_US"
USER_SYSTEM     = "android 11"
USER_DEVICE     = "firefox/128.0"

CATEGORY_ID   = "1921117247997878274"
PAGE_SIZE     = 10
MAX_PAGES     = 3
DELAY_SECONDS = 32
MAX_READS     = 20

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

# ─── Session Setup ─────────────────────────────────────────────────────────────
def setup_session():
    s = requests.Session()
    s.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "language": LANGUAGE,
        "X-User-System": USER_SYSTEM,
        "X-User-Device-Type": USER_DEVICE,
        "User-Agent": "Mozilla/5.0 Firefox/128.0"
    })
    return s

# ─── Compute MD5 hash ───────────────────────────────────────────────────────────
def make_hash(raw_password: str) -> str:
    return hashlib.md5(raw_password.encode()).hexdigest()

# ─── Fetch reading history ─────────────────────────────────────────────────────
def get_read_history(session):
    """
    Fetch all pages from worksHistory/pageHistory.
    Return a set of worksInfoId strings already read.
    """
    read_ids = set()
    page_no = 1
    while True:
        payload = {"pageNo": page_no, "pageSize": 50}
        resp = session.post(HISTORY_URL, json=payload)
        data = resp.json()
        if not data.get("success"):
            break
        for entry in data["result"]["list"]:
            read_ids.add(entry["worksInfoId"])
        if data["result"].get("isLastPage"):
            break
        page_no += 1
    return read_ids

# ─── Fetch content ID ───────────────────────────────────────────────────────────
def fetch_content_id(session, works_info_id):
    """
    Call getContent to retrieve worksInfoContentId for a given worksInfoId.
    Returns content_id string or None if not found.
    """
    resp = session.post(CONTENT_URL, json={"id": works_info_id})
    data = resp.json()
    if not data.get("success") or not data.get("result"):
        return None
    return data["result"][0]["id"]

# ─── Core Functions ─────────────────────────────────────────────────────────────
def login(session, phone, code):
    raw = f"password{code}"
    pw_hash = make_hash(raw)
    print(f"[{phone}] Using password hash: {pw_hash}")
    resp = session.post(LOGIN_URL, json={"phone": phone, "password": pw_hash})
    data = resp.json()
    if resp.status_code != 200 or not data.get("success"):
        raise RuntimeError(f"Login failed for {phone}: {data.get('message') or resp.text}")
    tok = data["result"]["token"]
    head = data["result"]["tokenHead"]
    auth = f"{head} {tok}"
    session.headers.update({
        "Authorization": auth,
        "memberInfoId": data["result"]["sysUserId"],
        "salesPersonId": SALES_PERSON_ID
    })
    print(f"[{phone}] ✔ Logged in")

def fetch_article_ids(session):
    """
    Grab up to MAX_READS worksInfoId values by paging through first MAX_PAGES.
    """
    ids = []
    for page in range(1, MAX_PAGES + 1):
        resp = session.post(PAGE_URL, json={
            "pageNo": page,
            "pageSize": PAGE_SIZE,
            "categoryId": CATEGORY_ID
        })
        data = resp.json()
        if not data.get("success"):
            print("⚠️ Failed to fetch page", page)
            break
        for item in data["result"]["list"]:
            if len(ids) >= MAX_READS:
                break
            ids.append(item["id"])
        if len(ids) >= MAX_READS:
            break
    return ids

def run_for_user(cred):
    session = setup_session()
    phone = cred["phone"]
    code  = cred["code"]

    try:
        # 1) Login
        login(session, phone, code)

        # 2) Fetch reading history
        print(f"[{phone}] Fetching reading history…")
        history_ids = get_read_history(session)
        print(f"[{phone}] {len(history_ids)} articles already read")

        # 3) Fetch article IDs
        article_ids = fetch_article_ids(session)
        if not article_ids:
            print(f"[{phone}] No articles found")
            return

        # 4) Process each ID if not in history
        claimed = 0
        for works_id in article_ids:
            if works_id in history_ids:
                print(f"[{phone}] ⏭️ {works_id} already read, skipping")
                continue

            # a) Fetch content ID for this worksInfoId
            content_id = fetch_content_id(session, works_id)
            if not content_id:
                print(f"[{phone}] ⚠️ No content for {works_id}, skipping")
                continue

            # b) startRead
            sr_resp = session.post(START_READ_URL, json={
                "worksInfoContentId": content_id,
                "worksInfoId": works_id
            })
            try:
                sr_data = sr_resp.json()
            except Exception:
                sr_data = sr_resp.text
            print(f"[{phone}] startRead({works_id}) → HTTP {sr_resp.status_code}, JSON: {sr_data}")

            # If server says AlreadyRead (businessMessage or code 1021), skip claim
            if not sr_data.get("success") and (
                sr_data.get("businessMessage") == "AlreadyRead" or sr_data.get("code") == 1021
            ):
                print(f"[{phone}] ⏭️ {works_id} marked AlreadyRead by server, skipping claim")
                continue

            # c) Wait DELAY_SECONDS
            print(f"[{phone}] Waiting {DELAY_SECONDS}s before claiming {works_id}…")
            time.sleep(DELAY_SECONDS)

            # d) claimReward
            cr_resp = session.post(CLAIM_URL, json={"worksInfoContentId": content_id})
            try:
                cr_data = cr_resp.json()
            except Exception:
                cr_data = cr_resp.text

            if cr_resp.status_code == 200 and isinstance(cr_data, dict) and cr_data.get("success"):
                print(f"[{phone}] 🎉 Claimed reward for {works_id}")
                claimed += 1
            else:
                print(f"[{phone}] ❌ claimReward({works_id}) failed: HTTP {cr_resp.status_code}, JSON: {cr_data}")

            if claimed >= MAX_READS:
                break

        print(f"[{phone}] {claimed}/{len(article_ids)} rewards claimed")

        # 5) Claim daily tier rewards
        print(f"[{phone}] 🔄 Claiming daily tier rewards…")
        resp = session.post(DAILY_INFO_URL, json={}).json()
        if resp.get("success"):
            for tier in resp["result"]["memberReadingRewardDetailVoList"]:
                if tier.get("memberReadingRewardStatus") == "complete":
                    num = tier.get("workInfoReadingNum")
                    r = session.post(DAILY_AWARD_URL, json={"workInfoReadingNum": num}).json()
                    if r.get("success"):
                        print(f"[{phone}] 🎁 Daily bonus for {num} articles claimed")
                    else:
                        print(f"[{phone}] ⚠️ Daily bonus claim for {num} failed")
        else:
            print(f"[{phone}] ❌ Failed to fetch daily rewards info")

        print(f"[{phone}] ✅ Done\n")

    except Exception as e:
        print(f"[{phone}] 🚨 Error: {e}\n")

# ─── Main Logic: Run Ten Accounts at a Time ───────────────────────────────────────
if __name__ == "__main__":
    print("🌟 Starting Bounty News Auto Claimer…\n")

    i = 0
    while i < len(credentials):
        batch = credentials[i : i + 50]
        threads = []
        for cred in batch:
            print(f"▶️ Starting thread for {cred['phone']}")
            t = threading.Thread(target=run_for_user, args=(cred,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        i += 50

    print("\n🏁 All tasks completed for all accounts.")
