from sqlalchemy import create_engine, inspect, text
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from data_models.database import DATABASE_URL

def inspect_database():
    print(f"Connecting to: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    print("\n--- Database Tables ---")
    table_names = inspector.get_table_names()
    if not table_names:
        print("No tables found in the database.")
        return

    with engine.connect() as conn:
        for table in table_names:
            # Get row count
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"- {table}: {count} rows")
                
                # Show columns for the first table as an example
                # columns = inspector.get_columns(table)
                # print(f"  Columns: {', '.join([c['name'] for c in columns])}")
            except Exception as e:
                print(f"- {table}: Error getting count ({e})")

if __name__ == "__main__":
    inspect_database()
