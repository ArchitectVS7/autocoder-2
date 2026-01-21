import sys
import asyncio
import json
import shutil
from pathlib import Path

# Set UTF-8 encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Use venv packages
sys.path.insert(0, str(Path("venv/Lib/site-packages")))

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

async def test_client():
    print("[TEST] Creating and entering client context...\n")
    
    test_dir = Path("test_aenter_project").resolve()
    test_dir.mkdir(exist_ok=True)
    
    # Create settings
    security_settings = {
        "sandbox": {"enabled": False},
        "permissions": {
            "defaultMode": "acceptEdits",
            "allow": ["Read(./**)", "Write(./**)", "Edit(./**)", "Glob(./**)"],
        },
    }
    settings_file = test_dir / ".claude_settings.json"
    with open(settings_file, "w") as f:
        json.dump(security_settings, f, indent=2)
    
    system_cli = shutil.which("claude")
    print(f"[INFO] Claude CLI: {system_cli}\n")
    
    try:
        client = ClaudeSDKClient(
            options=ClaudeAgentOptions(
                model="claude-opus-4-5-20251101",
                cli_path=system_cli,
                system_prompt="Test",
                allowed_tools=["Read", "Write", "Edit", "Glob"],
                permission_mode="acceptEdits",
                max_turns=100,
                cwd=str(test_dir.resolve()),
                settings=str(settings_file.resolve()),
            )
        )
        print("[OK] Client object created\n")
        
        print("[TEST] Entering async context (__aenter__)...")
        await client.__aenter__()
        print("[OK] Successfully entered context!")
        
        print("[TEST] Exiting context...")
        await client.__aexit__(None, None, None)
        print("[OK] Successfully exited context!")
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_client())
