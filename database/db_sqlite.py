import aiosqlite
from datetime import datetime

DATABASE = 'database/events.db'

async def init_db():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS event_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                total_events_count INTEGER,
                events_with_tickets_count INTEGER,
                events_without_tickets_count INTEGER,
                check_time TIMESTAMP
            )
        ''')
        await db.commit()

async def save_site_result_to_db(url, total_events_count, events_with_tickets_count, events_without_tickets_count):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
            INSERT INTO event_results (url, total_events_count, events_with_tickets_count, events_without_tickets_count, check_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (url, total_events_count, events_with_tickets_count, events_without_tickets_count, datetime.now()))
        await db.commit()

async def get_previous_results(url, limit=10):
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute('''
            SELECT events_with_tickets_count, total_events_count FROM event_results
            WHERE url = ? ORDER BY check_time DESC LIMIT ?
        ''', (url, limit)) as cursor:
            return await cursor.fetchall()