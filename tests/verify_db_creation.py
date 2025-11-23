import asyncio
import asyncpg
from sqlalchemy.engine.url import make_url
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import Config
from utils.db import init_db, engine

async def verify_db_creation():
    url = Config.DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    db_url = make_url(url)
    db_name = db_url.database
    user = db_url.username
    password = db_url.password
    host = db_url.host
    port = db_url.port

    print(f"Target Database: {db_name}")

    # 1. Drop the database if it exists (to simulate fresh start)
    try:
        sys_conn = await asyncpg.connect(
            user=user, password=password, host=host, port=port, database='postgres'
        )
        exists = await sys_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if exists:
            print(f"Dropping existing database '{db_name}' for testing...")
            # Terminate other connections first
            await sys_conn.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{db_name}'
                AND pid <> pg_backend_pid();
            """)
            await sys_conn.execute(f'DROP DATABASE "{db_name}"')
            print("Database dropped.")
        else:
            print("Database does not exist.")
        await sys_conn.close()
    except Exception as e:
        print(f"Error during setup (drop db): {e}")
        return

    # 2. Run init_db() which should create the DB
    print("Running init_db()...")
    try:
        await init_db()
        print("init_db() completed.")
    except Exception as e:
        print(f"init_db() failed: {e}")
        return

    # 3. Verify database exists
    try:
        sys_conn = await asyncpg.connect(
            user=user, password=password, host=host, port=port, database='postgres'
        )
        exists = await sys_conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        await sys_conn.close()
        
        if exists:
            print(f"SUCCESS: Database '{db_name}' exists.")
        else:
            print(f"FAILURE: Database '{db_name}' was NOT created.")
            
    except Exception as e:
        print(f"Error during verification: {e}")

if __name__ == "__main__":
    asyncio.run(verify_db_creation())
