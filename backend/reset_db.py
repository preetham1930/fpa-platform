import sys
import time
from backend.database import engine, Base
import backend.models

def main():
    print("=" * 60)
    print("WARNING: This script DROPS ALL DATA from the database.")
    print("All tables will be deleted and recreated.")
    print("=" * 60)
    
    # Adding a short sleep just in case someone runs it accidentally and wants to Ctrl+C
    time.sleep(3)
    
    print("Dropping all tables...")
    Base.metadata.drop_all(engine)
    
    print("Recreating all tables...")
    Base.metadata.create_all(engine)
    
    print("Database reset successfully! All tables recreated.")

if __name__ == "__main__":
    main()
