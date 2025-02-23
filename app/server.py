import requests
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

app = FastAPI()

DATABASE_NAME = "jars_data.db"

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            subtype TEXT,
            version TEXT,
            file TEXT,
            size_display TEXT,
            size_bytes INTEGER,
            md5 TEXT,
            built TEXT,
            stability TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def is_db_empty():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM jars')
    count = cursor.fetchone()[0]
    conn.close()
    return count == 0

def fetch_data():
    # Fetch all types
    types_url = 'https://centrojars.com/api/fetchJar/fetchAllTypes.php'
    print(f"Fetching types from: {types_url}")
    types_response = requests.get(types_url)
    types_data = types_response.json()
    print(f"Types response: {json.dumps(types_data, indent=2)}")

    all_files = []

    # Iterate over all types and subtypes
    for type_key, subtypes in types_data['response'].items():
        print(f"Processing type: {type_key}")
        for subtype in subtypes:
            print(f"Processing subtype: {subtype}")
            details_url = f'https://centrojars.com/api/fetchJar/{type_key}/{subtype}/fetchAllDetails.php'
            print(f"Fetching details from: {details_url}")
            details_response = requests.get(details_url)
            details_data = details_response.json()
            print(f"Details response: {json.dumps(details_data, indent=2)}")

            if details_data['status'] == 'success':
                for file_info in details_data['response']['files']:
                    file_entry = {
                        'Type': type_key,
                        'Subtype': subtype,
                        'Version': file_info['version'],
                        'File': file_info['file'],
                        'Size (Display)': file_info['size']['display'],
                        'Size (Bytes)': file_info['size']['bytes'],
                        'MD5': file_info['md5'],
                        'Built': file_info['built'],
                        'Stability': file_info['stability']
                    }
                    all_files.append(file_entry)
                    print(f"Added file entry: {file_entry}")

    return all_files

def save_to_db(data):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Insert all files into the database as a single snapshot
    for entry in data:
        cursor.execute('''
            INSERT INTO jars (type, subtype, version, file, size_display, size_bytes, md5, built, stability)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (entry['Type'], entry['Subtype'], entry['Version'], entry['File'], entry['Size (Display)'], entry['Size (Bytes)'], entry['MD5'], entry['Built'], entry['Stability']))

    conn.commit()
    conn.close()
    print(f"Saved {len(data)} entries to the database.")

def cleanup_old_entries():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Get the timestamps of the 3 most recent snapshots
    cursor.execute('''
        SELECT DISTINCT timestamp FROM jars ORDER BY timestamp DESC LIMIT 3
    ''')
    recent_timestamps = [row[0] for row in cursor.fetchall()]

    # Delete all entries that are not part of the 3 most recent snapshots
    if recent_timestamps:
        cursor.execute('''
            DELETE FROM jars WHERE timestamp NOT IN ({})
        '''.format(','.join(['?'] * len(recent_timestamps))), recent_timestamps)

    conn.commit()
    conn.close()
    print(f"Cleaned up old entries. Kept snapshots from: {recent_timestamps}")

def scheduled_job():
    print("Fetching data...")
    data = fetch_data()
    save_to_db(data)
    cleanup_old_entries()
    print("Data fetched and saved to DB.")

# Scheduler setup
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_job, 'cron', hour=12)  # Run daily at 12 PM
scheduler.start()

# Fetch data at the start if the database is empty or to get the latest updates
if is_db_empty():
    print("Database is empty. Fetching initial data...")
    scheduled_job()
else:
    print("Database is not empty. Fetching latest updates...")
    scheduled_job()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.get("/available")
async def get_data():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM jars ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()

    files = []
    for row in rows:
        files.append({
            'Type': row[1],
            'Subtype': row[2],
            'Version': row[3],
            'File': row[4],
            'Size (Display)': row[5],
            'Size (Bytes)': row[6],
            'MD5': row[7],
            'Built': row[8],
            'Stability': row[9],
            'Timestamp': row[10]
        })

    return JSONResponse(content={"files": files})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6969)
