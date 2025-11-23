import os
import sys
# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger

def test_logging():
    logger = get_logger()
    
    print("Testing logging...")
    logger.info("This is an INFO message.")
    logger.warning("This is a WARNING message.")
    logger.error("This is an ERROR message.")
    logger.debug("This is a DEBUG message (should be in file only).")
    
    # Check if file exists
    if os.path.exists("logs/app.log"):
        print("Log file created successfully.")
        with open("logs/app.log", "r") as f:
            content = f.read()
            print(f"Log file content length: {len(content)}")
            if "INFO" in content and "DEBUG" in content:
                print("Log file contains expected levels.")
            else:
                print("Log file missing expected levels.")
    else:
        print("Log file NOT created.")

if __name__ == "__main__":
    test_logging()
