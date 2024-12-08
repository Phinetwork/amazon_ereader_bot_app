import json

def migrate_progress_file():
    old_file = "progress.json"
    
    try:
        with open(old_file, "r") as f:
            old_progress = json.load(f)

        new_progress = {}

        for email, pages in old_progress.items():
            new_progress[email] = {
                "total_pages": pages,
                "books_read": {
                    "Unknown Book": pages  # Placeholder for book title
                }
            }

        with open(old_file, "w") as f:
            json.dump(new_progress, f, indent=4)
        
        print("Migration successful!")
    except Exception as e:
        print(f"Migration failed: {e}")

# Run the migration
migrate_progress_file()
