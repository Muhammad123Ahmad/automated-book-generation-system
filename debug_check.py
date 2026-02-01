import sys
import os
import traceback

print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")

try:
    print("Attempting imports...")
    from db import init_db
    from llm_client import generate_outline_from_llm
    from modules import outline, chapter, compile, notifications
    import main
    print("Imports successful.")
    
    print("Initializing DB...")
    init_db()
    print("DB Initialized.")
    
except Exception:
    traceback.print_exc()
