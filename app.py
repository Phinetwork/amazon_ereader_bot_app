from flask import Flask, render_template, request, redirect, url_for
import random
import time
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import os
import json
import threading

# Flask app setup
app = Flask(__name__)

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "bot_activity.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s")

# Global state to store live progress
live_progress = {
    "status": "Idle",
    "pages_read": 0,
    "email": None,
    "current_book": None,
}

progress_data = {}  # Store user progress (simulates a database)


def update_progress(email, pages_read):
    """Update progress for a specific user."""
    if email not in progress_data:
        progress_data[email] = {"total_pages": 0, "books_read": 0}
    progress_data[email]["total_pages"] += pages_read


def simulate_reading(driver, total_pages, delay_range, email):
    """Simulate reading for the given book."""
    global live_progress
    live_progress["status"] = "Reading"

    try:
        for page in range(total_pages):
            # Simulate reading by flipping pages
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.RIGHT)

            # Delay between page flips
            delay = random.randint(*delay_range)
            time.sleep(delay)

            # Update progress
            live_progress["pages_read"] += 1
            update_progress(email, 1)

    except Exception as e:
        logging.error(f"Error during reading: {e}")
        live_progress["status"] = f"Error: {e}"
    finally:
        live_progress["status"] = "Idle"


def start_bot_task(email, password, book_name, total_pages, delay_min, delay_max):
    """Start the bot task."""
    global live_progress
    live_progress["status"] = "Starting Bot..."
    live_progress["email"] = email
    live_progress["current_book"] = book_name
    live_progress["pages_read"] = 0

    # Configure Chrome options
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.binary_location = os.getenv("GOOGLE_CHROME_BIN", default="/usr/bin/google-chrome")

    try:
        driver = uc.Chrome(options=options)
        driver.get("https://read.amazon.com")
        logging.info("Opened Kindle Cloud Reader.")

        # Log in to Amazon
        driver.find_element(By.ID, "ap_email").send_keys(email)
        driver.find_element(By.ID, "ap_password").send_keys(password)
        driver.find_element(By.ID, "signInSubmit").click()
        time.sleep(5)  # Wait for login to complete

        # Select the book
        book_element = driver.find_element(By.XPATH, f"//span[text()='{book_name}']")
        book_element.click()
        time.sleep(5)  # Wait for the book to load

        # Start reading
        simulate_reading(driver, total_pages, (delay_min, delay_max), email)

        # Mark book as read
        progress_data[email]["books_read"] += 1

    except Exception as e:
        logging.error(f"Bot failed: {e}")
        live_progress["status"] = f"Error: {e}"
    finally:
        driver.quit()


@app.route("/", methods=["GET", "POST"])
def home():
    """Render the home page."""
    if request.method == "POST":
        # Get user inputs
        email = request.form["email"]
        password = request.form["password"]
        book_name = request.form["book_name"]
        total_pages = int(request.form["pages"])
        delay_min = int(request.form["delay_min"])
        delay_max = int(request.form["delay_max"])

        # Start the bot in a separate thread
        threading.Thread(
            target=start_bot_task,
            args=(email, password, book_name, total_pages, delay_min, delay_max),
        ).start()

        return redirect(url_for("dashboard"))

    return render_template("index.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    """Display the reading progress."""
    return render_template("dashboard.html", live_progress=live_progress, progress=progress_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
