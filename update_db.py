import sqlite3

# Connect to the database
conn = sqlite3.connect('campus_connect_v2.db')
cursor = conn.cursor()

try:
    # Add PIN column
    cursor.execute("ALTER TABLE item ADD COLUMN pin VARCHAR(10);")
    print("Added 'pin' column.")
except sqlite3.OperationalError:
    print("'pin' column already exists.")

try:
    # Add Image Hash column
    cursor.execute("ALTER TABLE item ADD COLUMN image_hash VARCHAR(50);")
    print("Added 'image_hash' column.")
except sqlite3.OperationalError:
    print("'image_hash' column already exists.")

conn.commit()
conn.close()
print("Database updated successfully!")