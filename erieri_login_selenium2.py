# erieri_login_selenium.py
"""
ERI login/session helper (drop-in).

Public API (unchanged):
    driver, is_logged_in = login_with_selenium(cookies_file="cookies.json")

What it does:
- Uses its own persistent Chrome profile folder: ./eri_profile (editable via ERI_USER_DATA_DIR)
  so cookies + localStorage persist across runs without fighting your personal Chrome profile.
- Loads cookies safely (correct domain handling, expiry cleanup) and refreshes.
- If still at /Account/Login, auto-logs in using either:
    * environment variables ERI_USER / ERI_PASS, or
    * ./eri_credentials.json  ->  {"username": "...", "password": "..."}
- Saves fresh cookies back to cookies_file on success.
- Light “stealth” tweaks to reduce soft login loops.
"""

import json, os, time
from pathlib import Path
from typing import Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException

HOME_URL  = "https://online.erieri.com/"
LOGIN_URL = "https://online.erieri.com/Account/Login"

def _log(msg): print(f"[eri-login] {msg}")

def _build_driver() -> webdriver.Chrome:
    opts = ChromeOptions()
    # Use a dedicated profile so we don't collide with a real Chrome that's open
    user_data_dir = os.getenv("ERI_USER_DATA_DIR", str(Path.cwd() / "eri_profile"))
    opts.add_argument(f"--user-data-dir={user_data_dir}")
    opts.add_argument("--window-size=1280,900")
    # Headless optional
    if os.getenv("ERI_HEADLESS", "0") == "1":
        opts.add_argument("--headless=new")
    # Gentle stealth
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--disable-blink-features=AutomationControlled")
    if os.getenv("ERI_CHROME_BINARY"):
        opts.binary_location = os.getenv("ERI_CHROME_BINARY")

    driver = webdriver.Chrome(options=opts)
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            """
        })
    except Exception:
        pass
    return driver

def _wait_ready(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def _is_on_login_page(driver) -> bool:
    url = (driver.current_url or "").lower()
    if "login" in url or "signin" in url:
        return True
    try:
        for e in driver.find_elements(By.CSS_SELECTOR, "input[type='password']"):
            if e.is_displayed():
                return True
    except Exception:
        pass
    return False

def _is_logged_in(driver) -> bool:
    if _is_on_login_page(driver):
        return False
    try:
        logout_xpath = (
            "//a[contains(translate(., 'LOGOUT','logout'),'logout')]"
            " | //button[contains(translate(., 'LOGOUT','logout'),'logout')]"
        )
        for e in driver.find_elements(By.XPATH, logout_xpath):
            if e.is_displayed():
                return True
    except Exception:
        pass
    return "account/login" not in (driver.current_url or "").lower()

def _sanitize_cookie(c: dict) -> dict:
    c = dict(c)
    if isinstance(c.get("expiry"), (str, type(None))):
        c.pop("expiry", None)
    for k in ("sameSite", "hostOnly"):
        c.pop(k, None)
    if "httpOnly" in c: c["httpOnly"] = bool(c["httpOnly"])
    if "secure" in c:   c["secure"]   = bool(c["secure"])
    return c

def _add_cookies_for_host(driver, cookies: list, host: str) -> int:
    added = 0
    driver.get(host); time.sleep(0.4)
    host_netloc = host.split("//", 1)[-1].strip("/").lower()
    for raw in cookies:
        c = _sanitize_cookie(raw)
        domain = (c.get("domain") or "").lstrip(".").lower()
        if not domain: continue
        if domain == host_netloc or host_netloc.endswith(domain):
            try:
                driver.add_cookie(c); added += 1
            except WebDriverException:
                pass
    return added

def _load_cookies_safely(driver, cookies_path: str) -> bool:
    p = Path(cookies_path)
    if not p.exists(): return False
    try:
        cookies = json.loads(p.read_text(encoding="utf-8"))
        driver.delete_all_cookies()
        total = 0
        total += _add_cookies_for_host(driver, cookies, HOME_URL)
        total += _add_cookies_for_host(driver, cookies, "https://erieri.com/")
        driver.get(HOME_URL)
        return total > 0
    except Exception:
        return False

def _save_fresh_cookies(driver, cookies_path: str):
    try:
        Path(cookies_path).write_text(json.dumps(driver.get_cookies(), indent=2), encoding="utf-8")
    except Exception:
        pass

def _read_creds():
    # Prefer environment, else ./eri_credentials.json next to this file or CWD
    user = os.getenv("ERI_USER")
    pw   = os.getenv("ERI_PASS")
    if user and pw:
        return user, pw
    for candidate in [Path.cwd()/ "eri_credentials.json", Path(__file__).with_name("eri_credentials.json")]:
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                u, p = data.get("username"), data.get("password")
                if u and p:
                    return u, p
            except Exception:
                pass
    return None, None

def _attempt_auto_login(driver) -> bool:
    user, pw = _read_creds()
    if not (user and pw):
        _log("No ERI_USER/ERI_PASS or eri_credentials.json; skipping auto-login.")
        return False

    driver.get(LOGIN_URL)
    try: _wait_ready(driver, 30)
    except TimeoutException: pass

    # Find inputs in a robust, generic way
    def find_first_displayed(selectors):
        for sel in selectors:
            try:
                if sel.startswith("//"):
                    els = driver.find_elements(By.XPATH, sel)
                else:
                    els = driver.find_elements(By.CSS_SELECTOR, sel)
                for e in els:
                    if e.is_displayed() and e.is_enabled():
                        return e
            except Exception:
                continue
        return None

    username_selectors = [
        "input#Email", "input#UserName", "input#Username",
        "input[name='Email']", "input[name='UserName']", "input[name='Username']",
        "input[type='email']", "input[type='text']"
    ]
    password_selectors = [
        "input#Password", "input[name='Password']", "input[type='password']"
    ]
    submit_selectors = [
        "button[type='submit']", "input[type='submit']",
        "//button[contains(translate(., 'LOGIN','login'),'login')]",
        "//button[contains(translate(., 'SIGN IN','sign in'),'sign in')]"
    ]

    u = find_first_displayed(username_selectors)
    p = find_first_displayed(password_selectors)
    if not (u and p):
        _log("Login form not detected; cannot auto-login.")
        return False

    try:
        u.clear(); u.send_keys(user); time.sleep(0.2)
        p.clear(); p.send_keys(pw)
        btn = find_first_displayed(submit_selectors)
        if btn:
            try: btn.click()
            except Exception: driver.execute_script("arguments[0].click();", btn)
        else:
            p.submit()
    except Exception:
        return False

    # Wait for post-login navigation
    for _ in range(60):
        time.sleep(1.0)
        if _is_logged_in(driver):
            return True
    return False

def login_with_selenium(cookies_file: str = "cookies.json") -> Tuple[webdriver.Chrome, bool]:
    _log("v2 helper loaded")
    driver = _build_driver()

    # Fast path: previously-authenticated profile
    driver.get(HOME_URL)
    try: _wait_ready(driver, 20)
    except TimeoutException: pass
    if _is_logged_in(driver):
        _log("Session already authenticated (profile).")
        _save_fresh_cookies(driver, cookies_file)
        return driver, True

    # Try cookies.json
    if _load_cookies_safely(driver, cookies_file):
        _log("Cookies loaded; checking session…")
        try: _wait_ready(driver, 15)
        except TimeoutException: pass
        if _is_logged_in(driver):
            _log("Authenticated via cookies.json.")
            _save_fresh_cookies(driver, cookies_file)
            return driver, True
        else:
            _log("Cookies present but not valid; continuing.")

    # Auto-login using creds
    if _attempt_auto_login(driver):
        _log("Authenticated via credentials.")
        _save_fresh_cookies(driver, cookies_file)
        return driver, True

    # Final state: not logged in (caller can decide what to do)
    _log("Unable to authenticate automatically.")
    driver.get(LOGIN_URL)
    try: _wait_ready(driver, 20)
    except TimeoutException: pass
    return driver, False