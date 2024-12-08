from flask import Flask, render_template, request, redirect, url_for, session
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
app.secret_key = "fb8d91a4c77b6d219d0d3aa8b5b14458e5fbe7a53c6e10ef3c34b867729a5945
"  # Replace with a secure key for session handling

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
        # Load existing progress or initialize new
        if os.path.exists(progress_file):
            with open(progress_file, "r") as f:
                progress = json.load(f)
        else:
            progress = {}

        # Update user's progress
        if email not in progress:
            progress[email] = {"total_pages": 0, "books_read": {}}

        progress[email]["total_pages"] += pages_read
        progress[email]["books_read"][book] = (
            progress[email]["books_read"].get(book, 0) + pages_read
        )

        # Save updated progress back to the file
        with open(progress_file, "w") as f:
            json.dump(progress, f, indent=4)

    except Exception as e:
        logging.error(f"Failed to update progress: {e}")


# Function to simulate reading
def simulate_reading(email, book, total_pages, delay_range):
    """Simulate reading by flipping pages one by one."""
    try:
        driver = drivers.get(email)
        if not driver:
            raise Exception("WebDriver not initialized for this user.")

        for page in range(total_pages):
            logging.info(f"{email} - Reading page {page + 1} of {book}")

            # Flip the page
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.RIGHT)

            # Simulate delay
            delay = random.randint(*delay_range)
            time.sleep(delay)

            # Update progress after flipping each page
            update_progress(email, 1, book)

    except Exception as e:
        logging.error(f"Error during reading simulation: {e}")


@app.route("/", methods=["GET", "POST"])
def home():
    """Main page where users input settings."""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")  # Optional for manual login
        total_pages = int(request.form.get("pages", 0))
        delay_min = int(request.form.get("delay_min", 0))
        delay_max = int(request.form.get("delay_max", 0))

        if not email or total_pages <= 0 or delay_min <= 0 or delay_max <= 0:
            return redirect(url_for("dashboard", error="Invalid input values."))

        # Initialize session data
        session["email"] = email
        session["pages"] = total_pages
        session["delay_min"] = delay_min
        session["delay_max"] = delay_max

        try:
            # Initialize WebDriver
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.binary_location = os.getenv("GOOGLE_CHROME_BIN", default="/usr/bin/google-chrome")

            drivers[email] = uc.Chrome(options=options)

            # Open Kindle Cloud Reader
            drivers[email].get("https://read.amazon.com")
            logging.info(f"{email} - Opened Kindle Cloud Reader.")

            # Allow the user to log in and choose a book
            session["current_book"] = select_book(drivers[email])
            return redirect(url_for("dashboard"))
        except Exception as e:
            logging.error(f"Error initializing WebDriver for {email}: {e}")
            return redirect(url_for("dashboard", error=str(e)))

    return render_template("index.html")


def select_book(driver):
    """Logic to dynamically select a book after login."""
    try:
        # Wait for the Kindle library to load
        time.sleep(10)  # Adjust the delay as needed

        # Locate books in the library and click the first available book
        books = driver.find_elements(By.CSS_SELECTOR, ".kindle-library-book")
        if not books:
            raise Exception("No books found in the library.")

        books[0].click()  # Click the first book
        logging.info("Selected the first book in the Kindle library.")

        # Extract the book title
        book_title = driver.find_element(By.CSS_SELECTOR, ".book-title").text
        logging.info(f"Book selected: {book_title}")

        return book_title
    except Exception as e:
        logging.error(f"Failed to select a book: {e}")
        return "Unknown Book"


@app.route("/dashboard")
def dashboard():
    """Display the user's reading progress and live status."""
    email = session.get("email", "N/A")
    current_book = session.get("current_book", "N/A")

    # Load progress from the file
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
        error=request.args.get("error"),
    )


@app.route("/start_bot")
def start_bot():
    """Start the bot for the logged-in user."""
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
            (session.get("delay_min", 5), session.get("delay_max", 10)),
        ),
    ).start()
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    """Clear the session and clean up resources."""
    email = session.get("email")
    if email and email in drivers:
        drivers[email].quit()
        del drivers[email]
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
