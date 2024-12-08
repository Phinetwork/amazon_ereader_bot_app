import tkinter as tk
from tkinter import simpledialog, messagebox
import random
import time
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import os


# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "bot_activity.log")
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(message)s")


def simulate_reading(driver, total_pages, delay_range):
    """Simulate reading by flipping pages one by one."""
    try:
        for page in range(total_pages):
            logging.info(f"Reading page {page + 1}")
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.RIGHT)
            delay = random.randint(*delay_range)
            logging.info(f"Waiting {delay} seconds before flipping to the next page...")
            time.sleep(delay)
    except Exception as e:
        logging.error(f"Error encountered: {e}")
        messagebox.showerror("Error", f"An error occurred while reading: {e}")


def start_bot(amazon_username, amazon_password, total_pages, delay_min, delay_max):
    """Initialize the bot and start the reading process."""
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Initialize WebDriver
    driver = uc.Chrome(options=options)

    try:
        # Log in to Kindle Cloud Reader
        driver.get("https://read.amazon.com")
        logging.info("Opened Kindle Cloud Reader.")
        messagebox.showinfo(
            "Log In",
            "Log in to your Amazon account manually, open the book, and then click OK to start reading.",
        )

        # Start reading
        simulate_reading(driver, total_pages, (delay_min, delay_max))

        messagebox.showinfo("Finished", "Finished reading the book!")
        logging.info("Finished reading all pages.")
    except Exception as e:
        logging.error(f"Critical error encountered: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        driver.quit()


def launch_gui():
    """Launch the GUI for user input."""
    root = tk.Tk()
    root.title("Amazon Reader Bot")

    # Labels and input fields
    tk.Label(root, text="Amazon Email:").grid(row=0, column=0, padx=10, pady=5)
    email_entry = tk.Entry(root, width=30)
    email_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(root, text="Amazon Password:").grid(row=1, column=0, padx=10, pady=5)
    password_entry = tk.Entry(root, width=30, show="*")
    password_entry.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(root, text="Total Pages to Read:").grid(row=2, column=0, padx=10, pady=5)
    pages_entry = tk.Entry(root, width=30)
    pages_entry.grid(row=2, column=1, padx=10, pady=5)

    tk.Label(root, text="Minimum Delay (seconds):").grid(row=3, column=0, padx=10, pady=5)
    delay_min_entry = tk.Entry(root, width=30)
    delay_min_entry.grid(row=3, column=1, padx=10, pady=5)

    tk.Label(root, text="Maximum Delay (seconds):").grid(row=4, column=0, padx=10, pady=5)
    delay_max_entry = tk.Entry(root, width=30)
    delay_max_entry.grid(row=4, column=1, padx=10, pady=5)

    def on_start():
        """Start the bot when the user clicks the Start button."""
        amazon_username = email_entry.get()
        amazon_password = password_entry.get()
        total_pages = int(pages_entry.get())
        delay_min = int(delay_min_entry.get())
        delay_max = int(delay_max_entry.get())

        if not amazon_username or not amazon_password:
            messagebox.showerror("Error", "Please enter your Amazon email and password.")
            return

        # Start the bot
        start_bot(amazon_username, amazon_password, total_pages, delay_min, delay_max)

    # Start button
    start_button = tk.Button(root, text="Start Reading", command=on_start, bg="green", fg="white")
    start_button.grid(row=5, column=0, columnspan=2, pady=10)

    # Run the GUI
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
