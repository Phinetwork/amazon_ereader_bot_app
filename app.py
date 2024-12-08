from flask import Flask, render_template, request, redirect, url_for, session
import random
import time
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import os
import json
import shutil
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask app setup
app = Flask(__name__)

# Retrieve secret key from environment
app.secret_key = os.getenv("FLASK_SECRET_KEY")  # Use the key from .env file

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "bot_activity.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s")

# Global state to store live progress
progress_file = "progress.json"
drivers = {}  # Store Selenium drivers per user session


# Function to update progress
def update_progress(email, pages_read, book):
    """Save the progress to a file."""
    try:
        if os.path.exists(progress_file):
            with open(progress_file, "r") as f:
                progress = json.load(f)
        else:
            progress = {}

        if email not in progress:
            progress[email] = {"total_pages": 0, "books_read": {}}

        progress[email]["total_pages"] += pages_read
        progress[email]["books_read"][book] = (
            progress[email]["books_read"].get(book, 0) + pages_read
        )

        with open(progress_file, "w") as f:
            json.dump(progress, f, indent=4)

    except Exception as e:
        logging.error(f"Failed to update progress: {e}")


# Function to simulate reading
def simulate_reading(email, book, total_pages, delay_range):
    """Simulate reading by flipping pages."""
    try:
        driver = drivers.get(email)
        if not driver:
            raise Exception("WebDriver not initialized for this user.")

        for page in range(total_pages):
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                body.send_keys(Keys.RIGHT)
                logging.info(f"{email} - Reading page {page + 1} of {book}")
                delay = random.randint(*delay_range)
                time.sleep(delay)
                update_progress(email, 1, book)
            except Exception as flip_error:
                logging.error(f"Error flipping page {page + 1}: {flip_error}")
                break
    except Exception as e:
        logging.error(f"Error during reading simulation: {e}")


@app.route("/", methods=["GET", "POST"])
def home():
    """Main page for user login."""
    if request.method == "POST":
        email = request.form.get("email")

        if not email:
            return render_template("index.html", error="Email is required.")

        session["email"] = email
        session["pages"] = 0  # Default value; updated on dashboard
        session["delay_min"] = 1  # Default value; updated on dashboard
        session["delay_max"] = 5  # Default value; updated on dashboard

        try:
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")

            # Dynamically locate Chrome binary
            chrome_binary = shutil.which("google-chrome") or shutil.which("chromium-browser")
            if not chrome_binary:
                raise FileNotFoundError("Chrome executable not found. Ensure Chrome is installed.")
            options.binary_location = chrome_binary

            drivers[email] = uc.Chrome(options=options)
            drivers[email].get("https://read.amazon.com")
            logging.info(f"{email} - Opened Kindle Cloud Reader.")

            session["current_book"] = select_book(drivers[email])
            return redirect(url_for("dashboard"))
        except Exception as e:
            logging.error(f"WebDriver initialization failed: {e}")
            return render_template("index.html", error="Failed to initialize WebDriver. Check logs.")

    return render_template("index.html")


def select_book(driver):
    """Logic to dynamically select a book."""
    try:
        time.sleep(10)
        books = driver.find_elements(By.CSS_SELECTOR, ".kindle-library-book")
        if not books:
            raise Exception("No books found in the library.")
        books[0].click()
        logging.info("Selected the first book in the Kindle library.")
        book_title = driver.find_element(By.CSS_SELECTOR, ".book-title").text
        return book_title
    except Exception as e:
        logging.error(f"Failed to select a book: {e}")
        return "Unknown Book"


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """Display reading progress and live status."""
    email = session.get("email", "N/A")
    current_book = session.get("current_book", "N/A")

    if request.method == "POST":
        try:
            delay_min = int(request.form.get("delay_min", 1))
            delay_max = int(request.form.get("delay_max", 5))
            pages = int(request.form.get("pages", 0))

            if delay_min <= 0 or delay_max <= 0 or delay_min > delay_max or pages <= 0:
                return redirect(url_for("dashboard", error="Invalid input values."))

            session["delay_min"] = delay_min
            session["delay_max"] = delay_max
            session["pages"] = pages
            logging.info(f"Settings updated: delay_min={delay_min}, delay_max={delay_max}, pages={pages}")
        except Exception as e:
            logging.error(f"Error updating settings: {e}")
            return redirect(url_for("dashboard", error="Failed to update settings."))

    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            progress = json.load(f)
    else:
        progress = {}
    current_progress = progress.get(email, {"total_pages": 0, "books_read": {}})
    return render_template(
        "dashboard.html",
        email=email,
        current_book=current_book,
        progress=current_progress,
        delay_min=session.get("delay_min", 1),
        delay_max=session.get("delay_max", 5),
        pages=session.get("pages", 0),
        error=request.args.get("error"),
    )


@app.route("/start_bot")
def start_bot():
    """Start the reading bot."""
    email = session.get("email")
    current_book = session.get("current_book")
    if not email or email not in drivers:
        return redirect(url_for("dashboard", error="Please log in and set up first."))

    threading.Thread(
        target=simulate_reading,
        args=(
            email,
            current_book,
            session.get("pages", 0),
            (session.get("delay_min", 1), session.get("delay_max", 5)),
        ),
    ).start()
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    """Clear session and resources."""
    email = session.get("email")
    if email and email in drivers:
        drivers[email].quit()
        del drivers[email]
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
