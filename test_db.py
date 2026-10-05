from utils.db import init_db, get_all_complaints

init_db()

print("Database initialized successfully!")

complaints = get_all_complaints()

print("Existing complaints:")
print(complaints)
