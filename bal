#!/usr/bin/env python3
import requests
import hashlib
import logging
import json
from pathlib import Path

# ─── Configuration Defaults ─────────────────────────────────────────────────────
API_BASE_URL    = "https://www.bounty-news.com/api"
LOGIN_URL       = f"{API_BASE_URL}/member/login"
USERINFO_URL    = f"{API_BASE_URL}/member/userInfo"

SALES_PERSON_ID = "232"
LANGUAGE        = "en_US"
USER_SYSTEM     = "android 11"
USER_DEVICE     = "firefox/128.0"

# ─── Logging Setup ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("balance_checker")

# ─── Credentials ────────────────────────────────────────────────────────────────
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

# ─── Helpers ────────────────────────────────────────────────────────────────────
def md5_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

def new_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "language": LANGUAGE,
        "X-User-System": USER_SYSTEM,
        "X-User-Device-Type": USER_DEVICE,
        "User-Agent": "Mozilla/5.0"
    })
    return s

# ─── Core Functions ─────────────────────────────────────────────────────────────
def login(session: requests.Session, phone: str, code: str) -> bool:
    pw = md5_hash(f"password{code}")
    resp = session.post(LOGIN_URL, json={"phone": phone, "password": pw})
    text = resp.text.strip()
    try:
        data = resp.json()
    except Exception:
        logger.error(f"[{phone}] Login: non-JSON response (HTTP {resp.status_code}): {text[:200]!r}")
        return False

    if resp.status_code != 200 or not data.get("success"):
        err = data.get("message") or text[:200]
        logger.error(f"[{phone}] Login failed: {err}")
        return False

    tok  = data["result"]["token"]
    head = data["result"]["tokenHead"]
    session.headers.update({
        "Authorization": f"{head} {tok}",
        "memberInfoId": str(data["result"]["sysUserId"]),
        "salesPersonId": SALES_PERSON_ID
    })
    logger.info(f"[{phone}] Logged in")
    return True

def fetch_balances(session: requests.Session, phone: str) -> dict:
    """Return balance, freezeBalance, useBalance as a dict."""
    resp = session.post(USERINFO_URL, json={})
    text = resp.text.strip()
    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"[{phone}] userInfo: non-JSON (HTTP {resp.status_code}): {text[:200]!r}")

    if resp.status_code != 200 or not data.get("success"):
        err = data.get("message") or text[:200]
        raise RuntimeError(f"[{phone}] userInfo failed: {err}")

    acct = data["result"].get("balanceAmtAccount", {})
    return {
        "balance": float(acct.get("balance", 0.0)),
        "freezeBalance": float(acct.get("freezeBalance", 0.0)),
        "useBalance": float(acct.get("useBalance", 0.0))
    }

# ─── Main Script ────────────────────────────────────────────────────────────────
def main():
    logger.info("🔍 Checking balances for all accounts...\n")
    results = []

    for cred in credentials:
        phone, code = cred["phone"], cred["code"]
        session = new_session()

        if not login(session, phone, code):
            results.append({"phone": phone, "error": "Login failed"})
            continue

        try:
            bal_dict = fetch_balances(session, phone)
            logger.info(f"[{phone}] Balance: {bal_dict['balance']} | Frozen: {bal_dict['freezeBalance']} | In-Use: {bal_dict['useBalance']}")
            rec = {"phone": phone, **bal_dict, "error": None}
        except Exception as e:
            logger.error(f"[{phone}] {e}")
            rec = {"phone": phone, "error": str(e)}

        results.append(rec)

    out = Path("balances.json")
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    logger.info(f"\n✅ Done. Results saved to {out.resolve()}")

if __name__ == "__main__":
    main()