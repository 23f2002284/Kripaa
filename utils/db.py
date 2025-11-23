from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.config import Config

# Ensure we use the async driver
DATABASE_URL = Config.DATABASE_URL
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

async def create_db_if_not_exists(url: str):
    from sqlalchemy.engine.url import make_url
    import asyncpg

    db_url = make_url(url)
    db_name = db_url.database
    
    # Connect to postgres database to check/create target db
    # Construct URL for default 'postgres' database
    if db_url.drivername == "postgresql+asyncpg":
        # We need to strip the +asyncpg part for make_url if we were to use it with some sync drivers, 
        # but here we are using asyncpg directly or via sqlalchemy.
        # Actually, let's just use the raw connection string for the postgres db.
        # We can reconstruct it.
        
        # Extract connection params
        user = db_url.username
        password = db_url.password
        host = db_url.host
        port = db_url.port
        
        try:
            # Connect to the default 'postgres' database
            sys_conn = await asyncpg.connect(
                user=user, password=password, host=host, port=port, database='postgres'
            )
            
            # Check if database exists
            exists = await sys_conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", db_name
            )
            
            if not exists:
                print(f"Database {db_name} does not exist. Creating...")
                await sys_conn.execute(f'CREATE DATABASE "{db_name}"')
                print(f"Database {db_name} created successfully.")
                
                # Close the connection to 'postgres' and connect to the new database to enable extensions
                await sys_conn.close()
                
                # Connect to the newly created database
                new_db_conn = await asyncpg.connect(
                    user=user, password=password, host=host, port=port, database=db_name
                )
                try:
                    print(f"Enabling 'vector' extension in {db_name}...")
                    await new_db_conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    print("'vector' extension enabled.")
                finally:
                    await new_db_conn.close()
                    
            else:
                # print(f"Database {db_name} already exists.")
                await sys_conn.close()
                
                # Ensure extension is enabled even if DB exists
                new_db_conn = await asyncpg.connect(
                    user=user, password=password, host=host, port=port, database=db_name
                )
                try:
                    # print(f"Ensuring 'vector' extension in {db_name}...")
                    await new_db_conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                finally:
                    await new_db_conn.close()

            
        except Exception as e:
            print(f"Warning: Could not check/create database: {e}")
            # Proceeding anyway, maybe it exists or we don't have permissions
            pass

async def init_db():
    await create_db_if_not_exists(DATABASE_URL)
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
