import os
import json
import asyncio
import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List
import aiofiles
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')

class DBConnection:
    def __init__(self,
                 host=DB_HOST,
                 port=DB_PORT,
                 user=DB_USER,
                 password=DB_PASSWORD,
                 database=DB_DATABASE,
                 logger=None,
                 use_json=False,
                 retry_attempts=5,
                 retry_delay=5,
                 backup_file='backup_sites.json'):
        self.host = host
        self.port = str(port)
        self.user = user
        self.password = password
        self.database = database
        self.use_json = use_json
        self.logger = logger
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.backup_file = self._get_backup_path(backup_file)
        self.pool = None

    @staticmethod
    def _get_backup_path(name) -> str:
        current_file_path = os.path.abspath(__file__)
        current_directory = os.path.dirname(current_file_path)
        backup_file_path = os.path.join(current_directory, name)
        return backup_file_path

    async def connect_db(self) -> None:
        for attempt in range(self.retry_attempts):
            try:
                self.pool = await asyncpg.create_pool(user=self.user,
                                                      password=self.password,
                                                      host=self.host,
                                                      port=self.port,
                                                      database=self.database)
                break
            except (asyncpg.PostgresError, OSError) as e:
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    if self.logger:
                        self.logger.error(f"Could not connect to the database after {self.retry_attempts} attempts.")
                    raise ConnectionError("Failed to connect to the database.")

    @asynccontextmanager
    async def get_cursor(self) -> AsyncGenerator[asyncpg.Connection, None]:
        if not self.pool:
            await self.connect_db()
        async with self.pool.acquire(timeout=30) as connection:
            async with connection.transaction():
                yield connection

    async def get_sites(self) -> List[str]:
        if self.use_json:
            return await self.load_backup_data()
        try:
            async with self.get_cursor() as conn:
                sites = await conn.fetch('SELECT name FROM public.tables_sites WHERE site_check=True')
                sites = [row['name'] for row in sites]
                await self.save_backup_data(sites)
                return sites
        except (Exception, asyncpg.PostgresError) as e:
            if self.logger:
                self.logger.error(f"Error fetching sites from the database: {e}")
            return await self.load_backup_data()

    async def save_backup_data(self, data) -> None:
        try:
            async with aiofiles.open(self.backup_file, 'w') as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving backup data: {e}")

    async def load_backup_data(self) -> List[str]:
        try:
            async with aiofiles.open(self.backup_file, 'r') as f:
                data = json.loads(await f.read())
            return data
        except FileNotFoundError:
            return []

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()

async def main():
    load_dotenv()
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_DATABASE = os.getenv('DB_DATABASE')

    db_connection = DBConnection(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE,
        use_json=False,
    )
    try:
        # Ensure the pool is connected
        await db_connection.connect_db()
        # Get sites
        sites = await db_connection.get_sites()
        print(f"Retrieved {len(sites)} sites from the database or backup.")
        for site in sites:
            print(site)
    except Exception as e:
        print(f"Error during database operation: {e}")
    finally:
        await db_connection.close()

if __name__ == '__main__':
    asyncio.run(main())