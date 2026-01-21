import sys
import json
import shutil
from pathlib import Path

# Set UTF-8 encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Use venv packages
sys.path.insert(0, str(Path("venv/Lib/site-packages")))

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

print("[TEST] Creating client with spec chat options...\n")

test_dir = Path("test_spec_project").resolve()
test_dir.mkdir(exist_ok=True)

# Create security settings (like spec_chat_session.py does)
security_settings = {
    "sandbox": {"enabled": False},
    "permissions": {
        "defaultMode": "acceptEdits",
        "allow": [
            "Read(./**)",
            "Write(./**)",
            "Edit(./**)",
            "Glob(./**)",
        ],
    },
}
settings_file = test_dir / ".claude_settings.json"
with open(settings_file, "w") as f:
    json.dump(security_settings, f, indent=2)

print(f"[INFO] Created settings file: {settings_file}")

system_cli = shutil.which("claude")
print(f"[INFO] Claude CLI: {system_cli}")
print(f"[INFO] Settings: {settings_file}")
print(f"[INFO] CWD: {test_dir}")
print()

try:
    client = ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model="claude-opus-4-5-20251101",
            cli_path=system_cli,
            system_prompt="Test system prompt",
            allowed_tools=["Read", "Write", "Edit", "Glob"],
            permission_mode="acceptEdits",
            max_turns=100,
            cwd=str(test_dir.resolve()),
            settings=str(settings_file.resolve()),
        )
    )
    print("[OK] Client created successfully!")
except Exception as e:
    print(f"[ERROR] Failed: {e}")
    import traceback
    traceback.print_exc()

