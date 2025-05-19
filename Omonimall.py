#!/usr/bin/env python3
import requests
import time
import hashlib
import threading
import random
from requests.exceptions import RequestException

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
MAX_PAGES     = 30
DELAY_SECONDS = 32
MAX_READS     = 50



# Retry configuration
MAX_RETRIES = 5
RETRY_DELAY_BASE = 5  # Base delay in seconds
RETRY_DELAY_MAX = 30  # Maximum delay in seconds

# ─── Credentials (phone + code) ────────────────────────────────────────────────
credentials = [
    {"phone": "09152077724", "code": "978"},
    {"phone": "09230555168", "code": "234"},
    {"phone": "09549107505", "code": "135"},
    {"phone": "09183321718", "code": "943"},
    {"phone": "09336396971", "code": "976"},
    {"phone": "09323257946", "code": "887"},
    {"phone": "09446321550", "code": "873"},
    {"phone": "09433996902", "code": "727"},
    {"phone": "09454360387", "code": "859"},
    {"phone": "09257099192", "code": "128"},
    {"phone": "09359009496", "code": "284"},
    {"phone": "09515243005", "code": "148"},
    {"phone": "09584891065", "code": "656"},
    {"phone": "09259292760", "code": "683"},
    {"phone": "09128230574", "code": "798"},
    {"phone": "09552467771", "code": "416"},
    {"phone": "09151769247", "code": "178"},
    {"phone": "09155062924", "code": "573"},
    {"phone": "09338305985", "code": "366"},
    {"phone": "09531799608", "code": "211"},
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

# ─── Enhanced HTTP Request with Retry Logic ───────────────────────────────────────
def make_request_with_retry(session, method, url, json_data=None, phone="Unknown", operation=""):
    """
    Make HTTP request with retry logic for handling temporary failures.
    
    Args:
        session: requests.Session object
        method: 'get' or 'post'
        url: URL to request
        json_data: JSON payload for POST requests
        phone: Phone number (for logging)
        operation: What operation is being performed (for logging)
        
    Returns:
        Response JSON object if successful
        
    Raises:
        RuntimeError if all retries fail
    """
    retries = 0
    last_error = None
    
    while retries <= MAX_RETRIES:
        try:
            if method.lower() == 'get':
                response = session.get(url)
            else:  # post
                response = session.post(url, json=json_data)
            
            # Check for HTTP errors
            if response.status_code >= 500:
                raise RequestException(f"Server error: HTTP {response.status_code}")
                
            # Try to parse JSON (may raise ValueError)
            data = response.json()
            
            # Log success
            if retries > 0:
                print(f"[{phone}] ✅ {operation} succeeded after {retries} retries")
                
            return data
            
        except (RequestException, ValueError, ConnectionError) as e:
            last_error = e
            retries += 1
            
            if retries > MAX_RETRIES:
                break
                
            # Calculate backoff delay with jitter
            delay = min(RETRY_DELAY_BASE * (2 ** (retries - 1)) + random.uniform(0, 1), RETRY_DELAY_MAX)
            print(f"[{phone}] ⚠️ {operation} failed (attempt {retries}/{MAX_RETRIES}): {str(e)}. Retrying in {delay:.1f}s...")
            time.sleep(delay)
    
    # If we get here, all retries failed
    raise RuntimeError(f"{operation} failed after {MAX_RETRIES} attempts: {str(last_error)}")

# ─── Fetch reading history ─────────────────────────────────────────────────────
def get_read_history(session, phone):
    """
    Fetch all pages from worksHistory/pageHistory.
    Return a set of worksInfoId strings already read.
    """
    read_ids = set()
    page_no = 1
    
    while True:
        payload = {"pageNo": page_no, "pageSize": 50}
        try:
            data = make_request_with_retry(
                session, 'post', HISTORY_URL, payload, 
                phone=phone, operation=f"fetch history page {page_no}"
            )
            
            if not data.get("success"):
                break
                
            for entry in data["result"]["list"]:
                read_ids.add(entry["worksInfoId"])
                
            if data["result"].get("isLastPage"):
                break
                
            page_no += 1
            
        except Exception as e:
            print(f"[{phone}] ⚠️ Error fetching history page {page_no}: {e}")
            break
            
    return read_ids

# ─── Fetch content ID ───────────────────────────────────────────────────────────
def fetch_content_id(session, works_info_id, phone):
    """
    Call getContent to retrieve worksInfoContentId for a given worksInfoId.
    Returns content_id string or None if not found.
    """
    try:
        data = make_request_with_retry(
            session, 'post', CONTENT_URL, {"id": works_info_id}, 
            phone=phone, operation=f"fetch content for {works_info_id}"
        )
        
        if not data.get("success") or not data.get("result"):
            return None
            
        return data["result"][0]["id"]
        
    except Exception as e:
        print(f"[{phone}] ⚠️ Error fetching content ID for {works_info_id}: {e}")
        return None

# ─── Core Functions ─────────────────────────────────────────────────────────────
def login(session, phone, code):
    raw = f"password{code}"
    pw_hash = make_hash(raw)
    print(f"[{phone}] Using password hash: {pw_hash}")
    
    try:
        data = make_request_with_retry(
            session, 'post', LOGIN_URL, {"phone": phone, "password": pw_hash}, 
            phone=phone, operation="login"
        )
        
        if not data.get("success"):
            raise RuntimeError(f"Login failed: {data.get('message')}")
            
        tok = data["result"]["token"]
        head = data["result"]["tokenHead"]
        auth = f"{head} {tok}"
        session.headers.update({
            "Authorization": auth,
            "memberInfoId": data["result"]["sysUserId"],
            "salesPersonId": SALES_PERSON_ID
        })
        print(f"[{phone}] ✔ Logged in")
        
    except Exception as e:
        print(f"[{phone}] 🚨 Login error: {e}")
        raise

def fetch_article_ids(session, phone):
    """
    Grab up to MAX_READS worksInfoId values by paging through first MAX_PAGES.
    """
    ids = []
    
    for page in range(1, MAX_PAGES + 1):
        try:
            data = make_request_with_retry(
                session, 'post', PAGE_URL, 
                {
                    "pageNo": page,
                    "pageSize": PAGE_SIZE,
                    "categoryId": CATEGORY_ID
                }, 
                phone=phone, operation=f"fetch page {page}"
            )
            
            if not data.get("success"):
                print(f"[{phone}] ⚠️ Failed to fetch page {page}")
                continue
                
            for item in data["result"]["list"]:
                if len(ids) >= MAX_READS:
                    break
                ids.append(item["id"])
                
            if len(ids) >= MAX_READS:
                break
                
        except Exception as e:
            print(f"[{phone}] ⚠️ Error fetching page {page}: {e}")
            continue
            
    return ids

def claim_daily_rewards(session, phone):
    """Claim daily tier rewards with retry logic"""
    print(f"[{phone}] 🔄 Claiming daily tier rewards...")
    
    try:
        resp = make_request_with_retry(
            session, 'post', DAILY_INFO_URL, {}, 
            phone=phone, operation="fetch daily rewards info"
        )
        
        if not resp.get("success"):
            print(f"[{phone}] ❌ Failed to fetch daily rewards info")
            return
            
        for tier in resp["result"]["memberReadingRewardDetailVoList"]:
            if tier.get("memberReadingRewardStatus") == "complete":
                num = tier.get("workInfoReadingNum")
                try:
                    r = make_request_with_retry(
                        session, 'post', DAILY_AWARD_URL, 
                        {"workInfoReadingNum": num}, 
                        phone=phone, operation=f"claim daily bonus for {num} articles"
                    )
                    
                    if r.get("success"):
                        print(f"[{phone}] 🎁 Daily bonus for {num} articles claimed")
                    else:
                        print(f"[{phone}] ⚠️ Daily bonus claim for {num} failed: {r.get('message')}")
                        
                except Exception as e:
                    print(f"[{phone}] ⚠️ Error claiming daily bonus for {num} articles: {e}")
                    
    except Exception as e:
        print(f"[{phone}] ❌ Error with daily rewards: {e}")

def run_for_user(cred):
    session = setup_session()
    phone = cred["phone"]
    code  = cred["code"]

    try:
        # 1) Login
        login(session, phone, code)

        # 2) Fetch reading history
        print(f"[{phone}] Fetching reading history...")
        history_ids = get_read_history(session, phone)
        print(f"[{phone}] {len(history_ids)} articles already read")

        # 3) Fetch article IDs
        article_ids = fetch_article_ids(session, phone)
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
            content_id = fetch_content_id(session, works_id, phone)
            if not content_id:
                print(f"[{phone}] ⚠️ No content for {works_id}, skipping")
                continue

            # b) startRead
            try:
                sr_data = make_request_with_retry(
                    session, 'post', START_READ_URL, 
                    {
                        "worksInfoContentId": content_id,
                        "worksInfoId": works_id
                    }, 
                    phone=phone, operation=f"startRead({works_id})"
                )
                
                print(f"[{phone}] startRead({works_id}) → {sr_data}")

                # If server says AlreadyRead (businessMessage or code 1021), skip claim
                if not sr_data.get("success") and (
                    sr_data.get("businessMessage") == "AlreadyRead" or sr_data.get("code") == 1021
                ):
                    print(f"[{phone}] ⏭️ {works_id} marked AlreadyRead by server, skipping claim")
                    continue
                    
            except Exception as e:
                print(f"[{phone}] ⚠️ Error in startRead for {works_id}: {e}")
                continue

            # c) Wait DELAY_SECONDS
            print(f"[{phone}] Waiting {DELAY_SECONDS}s before claiming {works_id}...")
            time.sleep(DELAY_SECONDS)

            # d) claimReward
            try:
                cr_data = make_request_with_retry(
                    session, 'post', CLAIM_URL, 
                    {"worksInfoContentId": content_id}, 
                    phone=phone, operation=f"claimReward({works_id})"
                )

                if cr_data.get("success"):
                    print(f"[{phone}] 🎉 Claimed reward for {works_id}")
                    claimed += 1
                else:
                    print(f"[{phone}] ❌ claimReward({works_id}) failed: {cr_data}")
                    
            except Exception as e:
                print(f"[{phone}] ❌ Error claiming reward for {works_id}: {e}")

            if claimed >= MAX_READS:
                break

        print(f"[{phone}] {claimed}/{len(article_ids)} rewards claimed")

        # 5) Claim daily tier rewards
        claim_daily_rewards(session, phone)

        print(f"[{phone}] ✅ Done\n")

    except Exception as e:
        print(f"[{phone}] 🚨 Error: {e}\n")

# ─── Main Logic: Run Multiple Accounts at a Time ───────────────────────────────────
if __name__ == "__main__":
    print("🌟 Starting Bounty News Auto Claimer with Retries...\n")

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
