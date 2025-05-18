#!/usr/bin/env python3
import hashlib
import random
import string
import requests

# --- CONFIGURATION ---
BASE_URL = "https://www.bounty-news.com"
REGISTRATION_URL = BASE_URL + "/api/userName/register"

INVITATION_CODE = "BMTWR2"   # ← your invitation code goes here
NUM_USERS = 5                # ← number of attempts/users per run

def random_phone():
    prefixes = ['091', '092', '093', '094', '095']
    return random.choice(prefixes) + ''.join(random.choices(string.digits, k=8))

def random_password():
    return "password" + str(random.randint(100, 999))

def md5_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

def generate_user_agent():
    return "Mozilla/5.0 (Android 11; Mobile; rv:128.0) Gecko/128.0 Firefox/128.0"

def register_account(phone, password, invitation_code):
    payload = {
        "phone": phone,
        "password": md5_hash(password),
        "matchPassword": md5_hash(password),
        "invitationCode": invitation_code,
        "userAgent": generate_user_agent()
    }
    headers = {
        "Content-Type": "application/json",
        "language": "en_US",
        "X-User-System": "Android 11",
        "X-User-Device-Type": "Firefox/128.0",
    }
    try:
        r = requests.post(REGISTRATION_URL, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        body = r.json()
        return body.get("success") and body.get("code") == 0
    except Exception:
        return False

def main():
    successful = []

    for _ in range(NUM_USERS):
        phone = random_phone()
        pwd = random_password()
        if register_account(phone, pwd, INVITATION_CODE):
            # strip "password" prefix to get only digits
            code_digits = pwd.replace("password", "")
            successful.append({
                "phone": phone,
                "code": code_digits
            })

    # print only the array of successful users
    print("successful = [")
    for entry in successful:
        print(f'    {{"phone": "{entry["phone"]}", "code": "{entry["code"]}"}},')
    print("]")

if __name__ == "__main__":
    main()