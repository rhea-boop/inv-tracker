import csv
import pymysql
import os
from dotenv import load_dotenv

# Load your database credentials
load_dotenv()

CSV_FILE = 'assets.csv' # Changed to assets.csv
TABLE_NAME = 'assets'   # Changed to the new table

print(f">>> READING {CSV_FILE}...")
assets_data = []
try:
    with open(CSV_FILE, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        for row in reader:
            assets_data.append(row)
except Exception as e:
    print(f"❌ Failed to read CSV: {e}")
    exit()

print(">>> CONNECTING TO DATABASE...")
try:
    db = pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD") or "",
        database=os.getenv("DB_NAME") # Make sure this is 'inventory_tracker' in your .env
    )
    cursor = db.cursor()
except Exception as e:
    print(f"❌ DATABASE CONNECTION FAILED: {e}")
    exit()

try:
    # 1. EXTRACT ALL EPCs FROM THE CSV
    # We use EPC as the source of truth, not ID.
    csv_epcs = [row['epc'] for row in assets_data if 'epc' in row]
    
    if not csv_epcs:
        print("❌ CRITICAL: Could not find an 'epc' column in the CSV.")
        exit()

    # 2. DELETE OLD ENTRIES
    # FIX: Delete based on EPC so we don't mix up strings and auto-increment integers
    format_strings = ','.join(['%s'] * len(csv_epcs))
    delete_query = f"DELETE FROM {TABLE_NAME} WHERE epc NOT IN ({format_strings})"
    cursor.execute(delete_query, tuple(csv_epcs))
    deleted_count = cursor.rowcount
    print(f">>> Removed {deleted_count} old entries from the database.")

    # 3. INSERT OR UPDATE CURRENT ENTRIES
    columns = ', '.join(headers)
    placeholders = ', '.join(['%s'] * len(headers))
    
    # Ignore 'id' if it accidentally gets left in the CSV, let the DB handle auto-increment
    updates = ', '.join([f"{col}=VALUES({col})" for col in headers if col != 'id'])
    
    insert_query = f"""
        INSERT INTO {TABLE_NAME} ({columns}) 
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {updates};
    """
    
    for row in assets_data:
        values = tuple(row[col] for col in headers)
        cursor.execute(insert_query, values)

    # 4. COMMIT TO THE DATABASE
    db.commit()
    print(f"✅ SUCCESS: Synced {len(assets_data)} assets with the database!")

except Exception as e:
    db.rollback()
    print(f"❌ SQL ERROR: {e}")
finally:
    db.close()