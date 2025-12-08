import time
import random
import os
import json
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

# --- CONFIGURATION ---
load_dotenv("config/.env")
COOKIE_FILE = "config/instagram_cookies.json"
MY_USERNAME = os.getenv("MY_USERNAME")
MY_PASSWORD = os.getenv("MY_PASSWORD")

def setup_driver_with_logging():
    mobile_emulation = { "deviceName": "iPhone 12 Pro" }

    chrome_options = Options()
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # --- CRITICAL STEP: ENABLE PERFORMANCE LOGGING ---
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_all_network_requests(driver, target_url_part="graphql/query"):
    """
    Captures ALL network requests matching the target_url_part.
    Returns a list of dictionaries.
    """
    print(f"Scanning network logs for ALL requests containing: '{target_url_part}' ...")

    # 1. Get all performance logs
    logs = driver.get_log("performance")

    captured_requests = []

    for entry in logs:
        try:
            log_json = json.loads(entry["message"])
            message = log_json["message"]

            # We look for the event when the request is sent
            if message["method"] == "Network.requestWillBeSent":
                request = message["params"]["request"]
                url = request["url"]

                # FILTER: Only keep POST requests that match our target URL
                if target_url_part in url and request["method"] == "POST":

                    # Extract Payload (postData)
                    payload = request.get("postData", None)

                    # Store valuable info
                    request_data = {
                        "url": url,
                        "timestamp": message["params"]["wallTime"], # Time it happened
                        "headers": request.get("headers", {}),
                        "payload": payload
                    }

                    captured_requests.append(request_data)

        except Exception as e:
            # Ignore log parsing errors
            continue

    return captured_requests

def human_type(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))

def mobile_swipe_up(driver):
    finger = PointerInput(interaction.POINTER_TOUCH, "finger")
    actions = ActionBuilder(driver, mouse=finger)
    viewport_width = driver.execute_script("return window.innerWidth")
    viewport_height = driver.execute_script("return window.innerHeight")

    start_x = int(viewport_width / 2)
    start_y = int(viewport_height * 0.8)
    end_y = int(viewport_height * 0.2)

    actions.pointer_action.move_to_location(start_x, start_y)
    actions.pointer_action.pointer_down()
    actions.pointer_action.pause(0.1)
    actions.pointer_action.move_to_location(start_x, end_y)
    actions.pointer_action.pointer_up()
    actions.perform()
    print("Swiped up successfully.")

def InstagramScraper(username):
    # 1. Setup Driver
    driver = setup_driver_with_logging()
    wait = WebDriverWait(driver, 15)

    try:
        print("1. Navigating to Instagram...")
        driver.get("https://www.instagram.com/")

        # --- COOKIE POPUP HANDLER ---
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept') or contains(text(), 'Only allow essential cookies')]"))
            )
            cookie_button.click()
            print("Accepted Cookies Popup.")
            time.sleep(2)
        except TimeoutException:
            print("No Cookie Popup found.")

        # =================================================================
        # NEW LOGIC: CHECK & LOAD SAVED COOKIES
        # =================================================================
        need_to_login = True  # Default to True

        if os.path.exists(COOKIE_FILE):
            print(f"Found {COOKIE_FILE}. Attempting to restore session...")

            with open(COOKIE_FILE, "r") as file:
                cookies = json.load(file)

            for cookie in cookies:
                # Cleaning up cookie data for Selenium
                if 'domain' in cookie: del cookie['domain']
                try: driver.add_cookie(cookie)
                except: pass

            print("Cookies injected. Refreshing page...")
            driver.refresh()
            time.sleep(5) # Wait for page to reload

            # VERIFICATION: Are we logged in?
            if "Log in" not in driver.page_source:
                print(">>> SUCCESS: Logged in via Cookies! Skipping login steps.")
                need_to_login = False
            else:
                print(">>> FAIL: Cookies expired. Proceeding to manual login.")
                need_to_login = True

        # =================================================================
        # CONDITIONAL LOGIN EXECUTION
        # =================================================================
        if need_to_login:
            print("--- Starting Manual Login Process ---")

            # Swipe up
            mobile_swipe_up(driver)

            # Click Initial Login Button
            try:
                print("Looking for initial Log in button...")
                login_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Log in']]"))
                )
                login_btn.click()
            except:
                # Sometimes we are already on the form
                print("Could not click 'Log in' button (maybe already on form?)")

            # Input Credentials
            print("Waiting for username field...")
            username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))

            # Type Username
            username_input.click()
            human_type(username_input, MY_USERNAME)
            time.sleep(1)

            # Type Password
            password_input = driver.find_element(By.NAME, "password")
            password_input.click()
            human_type(password_input, MY_PASSWORD)
            time.sleep(1)

            # Click Submit
            try:
                print("Clicking Submit...")
                submit_btn = driver.find_element(By.XPATH, "//div[@role='button' and @aria-label='Log in']")
                submit_btn.click()
            except:
                # Fallback
                driver.find_element(By.XPATH, "//button[@type='submit']").click()

            # Wait for Login to process
            print("Waiting for login to complete...")
            time.sleep(8)

            # Save the new valid cookies for next time
            print("Saving new cookies...")
            with open(COOKIE_FILE, "w") as file:
                json.dump(driver.get_cookies(), file)

        # =================================================================
        # SCRAPING STARTS HERE
        # =================================================================
        print("\n--- READY TO SCRAPE ---")
        print(f"Current URL: {driver.current_url}")

        # Example: Get User Profile
        target_profile = f"https://www.instagram.com/{username}/"
        driver.get(target_profile)

        print("Waiting for login to complete...")
        time.sleep(random.uniform(6, 8))

        # -------------------------------------------------------------
        # STUBBORN POPUP HANDLER
        # -------------------------------------------------------------
        print("Attempting to handle 'Save Login Info' popup...")

        popup_attempts = 0
        max_attempts = 3

        while popup_attempts < max_attempts:
            try:
                # 1. CHECK IF POPUP EXISTS
                popup_indicator = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Not now')] | //*[@aria-label='Close']"))
                )
                print(f"Popup detected (Attempt {popup_attempts+1})...")

                # 2. TRY CLICKING "NOT NOW" FIRST
                try:
                    # Find the button specifically
                    not_now_btn = driver.find_element(By.XPATH, "//div[@role='button' and contains(., 'Not now')]")

                    # Method A: JavaScript Click (The strongest click)
                    driver.execute_script("arguments[0].click();", not_now_btn)
                    print(" > Clicked 'Not now' (JS)...")
                    time.sleep(1) # Wait to see if it worked

                    # Method B: If it's still there, try ActionChains (Touch simulation)
                    if "Not now" in driver.page_source:
                        print(" > JS Click didn't work. Trying Touch Action...")
                        ActionChains(driver).move_to_element(not_now_btn).click().perform()
                        time.sleep(1)

                except:
                    print(" > Could not find 'Not now' button, switching to 'X' button...")

                # 3. IF "NOT NOW" FAILED, CLICK THE "X" BUTTON
                # Check if the popup is still there
                if "Save your login info?" in driver.page_source:
                    try:
                        # The X button usually has aria-label="Close"
                        close_btn = driver.find_element(By.XPATH, "//*[@aria-label='Close']")
                        driver.execute_script("arguments[0].click();", close_btn)
                        print(" > Clicked 'X' button...")
                        time.sleep(1)
                    except:
                        pass

                # 4. VERIFY IF GONE
                if "Save your login info?" not in driver.page_source:
                    print("SUCCESS: Popup is gone!")
                    break # Exit the loop

            except TimeoutException:
                print("Popup did not appear (or is already gone).")
                break

            popup_attempts += 1
            time.sleep(1) # Pause before next retry

        # -------------------------------------------------------------
        # END OF POPUP HANDLER
        # -------------------------------------------------------------

        print(f"Visited profile: {username}")
        driver.save_screenshot(f"ss/{username}_profile_page.png")

        # 2. Trigger the Network Request
        time.sleep(5) # Wait for network requests to fire

        # 3. Extract the Data
        all_data = get_all_network_requests(driver, "graphql/query")

        print(f"\n>>> FOUND {len(all_data)} REQUESTS <<<\n")

        for index, req in enumerate(all_data):
            # print("="*60)
            # print(f"REQUEST #{index + 1}")
            # print(f"URL: {req['url']}")
            # print("-" * 20)

            # print("HEADERS:")
            # # Pretty print headers
            # print(json.dumps(req['headers'], indent=2))

            # print("-" * 20)
            # print("PAYLOAD:")

            if req['payload']:
                try:
                    # Try to parse payload as JSON to make it readable
                    parsed_payload = json.loads(req['payload'])
                    #print(json.dumps(parsed_payload, indent=2))
                except:
                    # If it's not JSON (e.g., raw string or url-encoded), print as is
                    print(req['payload'])
            else:
                print("[No Payload / Empty Body]")

            print("="*60 + "\n")

        # Assuming 'all_data' is your list from the previous step
        if len(all_data) >= 5:

          # Use a Session for better performance (reuses the connection)
          session = requests.Session()

          print(f"Starting replay of {len(all_data)} requests...")

          # FIX: Use 'enumerate' to get both the index (i) and the item (raw_request)
          for i, raw_request in enumerate(all_data):

              print(f"\n--- Processing Request #{i + 1} ---")
              print(f"URL: {raw_request['url']}")

              # 1. CLEAN HEADERS
              clean_headers = {}
              for key, value in raw_request['headers'].items():
                  # Remove HTTP/2 headers and length/encoding headers
                  if not key.startswith(':') and key.lower() not in ['content-length', 'accept-encoding']:
                      clean_headers[key] = value

              # 2. SEND REQUEST
              try:
                  response = session.post(
                      raw_request['url'],
                      headers=clean_headers,
                      data=raw_request['payload']
                  )

                  print(f"Status: {response.status_code}")

                  # 3. SAVE JSON
                  if response.status_code == 200:
                      try:
                          # Parse JSON
                          data = response.json()

                          # Create a unique filename for each request
                          output_file = f"data/raw/{username}/request_{i}_result.json"

                          # Create the folder if it doesn't exist
                          os.makedirs(os.path.dirname(output_file), exist_ok=True)

                          with open(output_file, "w", encoding="utf-8") as f:
                              json.dump(data, f, indent=4)

                          print(f"SUCCESS: Saved to '{output_file}'")

                      except json.JSONDecodeError:
                          print("Warning: Request succeeded (200 OK) but response was not JSON.")
                  else:
                      print(f"Failed. Response: {response.text[:100]}...")

              except Exception as e:
                  print(f"Error processing request #{i}: {e}")

        else:
            print("Not enough data captured (Need at least 5 requests).")

    except Exception as e:
        print(f"Error: {e}")
        driver.save_screenshot(f"ss/{username}_error_final.png")

    finally:
       driver.quit()
