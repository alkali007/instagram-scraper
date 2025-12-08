# Test for Scrapping Specialist

**Mobile Application:** Instagram  
**Objective:** Extract Profile Page using account name as the input parameter  
**Programming Language:** Python  

---

## Documentation

### A. Step to build and run the Docker container
To deploy the scraper, use the following Docker commands.

**1. Build the image:**
```bash
docker build -t insta-scrape .
```

**2. Run the container:**
```bash
docker run --rm -v $(pwd)/data:/app/data insta-scrape username (example: paragoncorp)
```

### B. How to simulate a real mobile session
This project utilizes Chrome Device Emulation via Selenium. This allows the WebDriver to render pages exactly as they would appear on a mobile device by overriding the User-Agent and viewport settings.

**Implementation:**  
ChromeOptions are configured to enable mobile emulation, allowing the scraper to switch between various device profiles (e.g., iPhone 12 Pro, Samsung Galaxy S8+, Pixel 5).

### C. How to rotate device fingerprints
To prevent detection, the system ensures consistency between the network and the browser environment:

*   **User-Agents:** Maintains a list of valid User-Agent strings from real mobile devices.
*   **Viewport Matching:** When a User-Agent is selected, the browser viewport (resolution) is automatically adjusted to match that specific device to ensure the fingerprint is consistent.

### D. How to avoid rate limits
The scraper employs a strategy to stay within platform limits:

*   **Throttling:** Implements randomized time delays (`time.sleep`) between actions to mimic human hesitation.
*   **Request Limits:** Enforces a maximum number of requests per session or per minute to ensure the scraper does not trigger API flooding protections.

### E. How to refresh tokens
When a session expires, Selenium is used to refresh the authentication state without a full login:

*   Trigger a page reload/refresh using the WebDriver.
*   Extract the newly generated cookies and headers.
*   Inject these new cookies back into the session handler to maintain access.

### F. How to solve Captcha
**Prevention Strategy:**
*   **High-Quality Proxies:** Uses Residential or Mobile 4G/5G proxies rather than Data Center IPs.
*   **Geo-Targeting:** The proxy location must match the target site's region (e.g., if targeting Shopee Indonesia, use an Indonesian residential proxy).
*   **Fingerprint Alignment:** The User-Agent language and time zone settings are synced with the proxy location.

**Solving Strategy:**
*   **Solving Services:** If a Captcha appears, the system integrates with third-party solving services (such as 2Captcha, Anti-Captcha, or CapSolver).
*   **Advanced AI:** For complex puzzles, computer vision models combined with Selenium actions can be implemented to solve them natively.

### G. How to mimic touch events or app-like behaviour
Since mobile sites expect touch interactions rather than mouse clicks, the scraper uses Selenium's advanced input controls:

*   **Pointer Input / Action Chains:** Utilizes the W3C Pointer Input standard to simulate "tap," "swipe," and "scroll" gestures, ensuring the behavior is indistinguishable from a user touching a physical screen.
