import sys
import asyncio
from pathlib import Path
import shutil
import os

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Activate venv first
venv_python = Path("venv/Scripts/python.exe")
if not venv_python.exists():
    print("[ERROR] Virtual environment not found!")
    sys.exit(1)

# Import from venv
sys.path.insert(0, str(Path("venv/Lib/site-packages")))

try:
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
    print("[OK] Claude SDK imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import Claude SDK: {e}")
    sys.exit(1)

# Try to create a minimal client
print("\n[TEST] Creating Claude SDK client...")

try:
    test_dir = Path("test_project").resolve()
    test_dir.mkdir(exist_ok=True)
    
    system_cli = shutil.which("claude")
    print(f"[INFO] Claude CLI path: {system_cli}")
    
    # Make sure PATH is set
    print(f"[INFO] PATH has npm dir: {'npm' in os.environ.get('PATH', '')}")
    
    client = ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model="claude-sonnet-4-5-20250929",
            cli_path=system_cli,
            cwd=str(test_dir),
            allowed_tools=["Read", "Write"],
            max_turns=1
        )
    )
    print("[OK] Client created successfully!")
    
except Exception as e:
    print(f"[ERROR] Failed to create client: {e}")
    import traceback
    traceback.print_exc()

