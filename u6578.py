import requests
import random
import string
import hashlib
import time
import json
import threading
import queue
import uuid
import urllib3

# Disable SSL warnings (insecure)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Function to generate a random email address
def generate_random_email():
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "protonmail.com"]
    domain = random.choice(domains)
    return f"{username}@{domain}"

# Function to compute MD5 hash of the password
def create_md5_hash(password):
    return hashlib.md5(password.encode()).hexdigest()

# Worker function for threads
def worker(task_queue, results, lock, password_hash, user_type, code, disable_ssl):
    url = "https://api.u6578.me/api/user/register?lang=en"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "st-lang": "en",
        # st-ttgn and st-ctime will be set per-request below
        "User-Agent": "Mozi"
    }

    while True:
        try:
            task_queue.get_nowait()
        except queue.Empty:
            return

        # Prepare timestamp and unique header
        current_time = int(time.time() * 1000)
        headers["st-ctime"] = str(current_time)
        headers["st-ttgn"] = uuid.uuid4().hex

        email = generate_random_email()
        payload = {
            "account": email,
            "pwd": password_hash,
            "user_type": user_type,
            "code": code,
            "telegram": "",
            "whatsapp": "",
            "captcha": ""
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                verify=not disable_ssl
            )
            print(f"Thread {threading.current_thread().name} - Email: {email} - Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 200:
                    token = data.get('data', {}).get('token')
                    with lock:
                        results.append({
                            'email': email,
                            'password_hash': password_hash,
                            'password_clear': None,
                            'token': token
                        })
                    print(f"✓ Success ({len(results)} total)")
                else:
                    print(f"✗ Failed: {data.get('msg', 'Unknown error')}")
            else:
                print(f"✗ HTTP {response.status_code}")

        except Exception as e:
            print(f"✗ Exception: {e}")

        finally:
            time.sleep(1)
            task_queue.task_done()

# Main interactive CLI
if __name__ == '__main__':
    try:
        count = int(input('How many accounts would you like to create? '))
    except ValueError:
        print('Invalid number. Exiting.')
        exit(1)

    try:
        threads = int(input('How many threads to use? (e.g., 1-10) '))
    except ValueError:
        threads = 1
        print('Invalid threads input; defaulting to 1.')

    code = input('Enter the referral/invitation code: ').strip()
    if not code:
        print('Invitation code cannot be empty. Exiting.')
        exit(1)

    password = input('Enter a strong password to use for all accounts (leave blank for default): ')
    if not password:
        password = 'StrongPassword123!'
        print(f'Using default password: {password}')

    disable_ssl_input = input('Disable SSL verification? [y/N]: ').strip().lower()
    disable_ssl = disable_ssl_input == 'y'
    if disable_ssl:
        print('Warning: SSL verification is disabled. This is insecure.')

    password_hash = create_md5_hash(password)
    user_type = 1  # default user_type

    # Prepare task queue and shared results
    task_queue = queue.Queue()
    for _ in range(count):
        task_queue.put(1)

    results = []
    lock = threading.Lock()

    # Start worker threads
    for i in range(max(1, threads)):
        t = threading.Thread(
            target=worker,
            name=f'Worker-{i+1}',
            args=(task_queue, results, lock, password_hash, user_type, code, disable_ssl)
        )
        t.start()

    # Wait for all tasks to complete
    task_queue.join()

    # Summary and save outputs
    print(f"\nTotal successful registrations: {len(results)}/{count}")

    # Save simple list (email:password)
    with open('registered_accounts.txt', 'w') as f:
        for entry in results:
            f.write(f"{entry['email']}:{password}\n")
    print("Saved simple credentials to registered_accounts.txt")

    # Save full JSON details
    with open('registered_accounts_full.json', 'w') as f:
        json.dump(results, f, indent=4)
    print("Saved full details to registered_accounts_full.json")

