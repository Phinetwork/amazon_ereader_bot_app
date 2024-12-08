from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import random
from fake_useragent import UserAgent
import undetected_chromedriver as uc

# Function to simulate random human-like delays
def random_delay(min_time=30, max_time=60):
    return random.randint(min_time, max_time)

# Function to flip pages and simulate reading
def flip_pages(driver, total_pages=50):
    for page in range(total_pages):
        print(f"Flipping to page {page + 1}...")
        # Simulate flipping the page
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.RIGHT)
        delay = random_delay()
        print(f"Waiting {delay} seconds before flipping the next page...")
        time.sleep(delay)

# Main function
def main():
    # Configure a random user agent
    ua = UserAgent()
    user_agent = ua.random
    print(f"Using User Agent: {user_agent}")

    # Configure Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Uncomment the following to add proxy support
    # options.add_argument('--proxy-server=http://your-proxy:port')

    # Use undetected-chromedriver to bypass bot detection
    driver = uc.Chrome(options=options)

    # Navigate to Kindle Cloud Reader
    print("Opening Kindle Cloud Reader...")
    driver.get("https://read.amazon.com")

    # Prompt user to log in
    print("Log in to your Amazon account and open the book manually...")
    input("Press Enter once the book is open...")

    # Simulate reading the eBook
    print("Starting to flip pages...")
    flip_pages(driver, total_pages=50)

    # Close the browser
    print("Finished reading. Closing browser...")
    driver.quit()

if __name__ == "__main__":
    main()
