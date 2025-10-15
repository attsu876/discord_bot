import sys
import os
import asyncio

# Add project root to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
os.chdir(PROJECT_ROOT)
sys.path.append(PROJECT_ROOT)

from main import main

if __name__ == "__main__":
    asyncio.run(main())