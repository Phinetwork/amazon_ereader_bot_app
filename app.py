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
}

# Function to update progress
def update_progress(email, pages_read):
    """Save the progress to a file."""
    progress_file = "progress.json"

    try:
        # Load existing progress or initialize new
        if os.path.exists(progress_file):
            with open(progress_file, "r") as f:
                progress = json.load(f)
        else:
            progress = {}

        # Update user's progress
        progress[email] = progress.get(email, 0) + pages_read

        # Save updated progress back to the file
        with open(progress_file, "w") as f:
            json.dump(progress, f, indent=4)

    except Exception as e:
        logging.error(f"Failed to update progress: {e}")


# Function to simulate reading
def simulate_reading(driver, total_pages, delay_range, email):
    """Simulate reading by flipping pages one by one."""
    global live_progress
    live_progress["status"] = "Reading"

    try:
        for page in range(total_pages):
            live_progress["pages_read"] += 1
            logging.info(f"Reading page {page + 1}")
            
            # Flip the page
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.RIGHT)
            
            # Simulate delay
            delay = random.randint(*delay_range)
            logging.info(f"Waiting {delay} seconds before flipping to the next page...")
            time.sleep(delay)

            # Update progress after flipping each page
            update_progress(email, 1)

    except Exception as e:
        logging.error(f"Error encountered while reading: {e}")
        live_progress["status"] = f"Error: {e}"
    finally:
        live_progress["status"] = "Idle"


@app.route("/", methods=["GET", "POST"])
def home():
    """Main page where users input settings."""
    global live_progress

    if request.method == "POST":
        try:
            # Collect user inputs
            amazon_username = request.form.get("email")
            total_pages = int(request.form.get("pages", 0))
            delay_min = int(request.form.get("delay_min", 0))
            delay_max = int(request.form.get("delay_max", 0))

            if not amazon_username or total_pages <= 0 or delay_min <= 0 or delay_max <= 0:
                raise ValueError("Invalid input values.")

            # Initialize Chrome options
            options = uc.ChromeOptions()
            options.add_argument("--headless")  # Use headless mode for server deployment
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--start-maximized")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.binary_location = os.getenv("GOOGLE_CHROME_BIN", default="/usr/bin/google-chrome")

            try:
                driver = uc.Chrome(options=options)
            except Exception as e:
                logging.error(f"WebDriver initialization failed: {e}")
                live_progress["status"] = f"WebDriver Error: {e}"
                return redirect(url_for("dashboard"))

            # Update live progress
            live_progress["status"] = "Opening Kindle Cloud Reader"
            live_progress["email"] = amazon_username
            live_progress["pages_read"] = 0

            # Open Kindle Cloud Reader
            driver.get("https://read.amazon.com")
            logging.info("Opened Kindle Cloud Reader.")

            # Notify user to manually log in
            live_progress["status"] = "Waiting for manual login and book selection..."
            time.sleep(60)  # Allow the user to log in and select a book manually

            # Start reading in a separate thread
            threading.Thread(
                target=simulate_reading, args=(driver, total_pages, (delay_min, delay_max), amazon_username)
            ).start()

            return redirect(url_for("dashboard"))
        except ValueError as ve:
            logging.error(f"Validation error: {ve}")
            live_progress["status"] = "Validation Error: Check your input."
            return redirect(url_for("dashboard"))
        except Exception as e:
            logging.error(f"Critical error encountered: {e}")
            live_progress["status"] = f"Error: {e}"
            return redirect(url_for("dashboard"))

    return render_template("index.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    """Display the user's reading progress and live status."""
    progress_file = "progress.json"

    # Load progress from the file
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            progress = json.load(f)
    else:
        progress = {}

    # Display only current user's progress
    current_email = live_progress.get("email")
    current_progress = progress.get(current_email, 0)

    # Render the dashboard
    return render_template(
        "dashboard.html",
        progress={current_email: current_progress} if current_email else {},
        live_progress=live_progress,
        current_progress=current_progress,
    )


@app.route("/start_bot", methods=["GET"])
def start_bot():
    """Manually start the bot via dashboard button."""
    global live_progress
    live_progress["status"] = "Starting Bot..."
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    # Bind to all network interfaces and set port for production
    app.run(host="0.0.0.0", port=8080)
