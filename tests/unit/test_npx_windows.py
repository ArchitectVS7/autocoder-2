import subprocess
import shutil

# Check if npx.cmd exists
npx_path = shutil.which("npx")
npx_cmd_path = shutil.which("npx.cmd")

print(f"shutil.which('npx'): {npx_path}")
print(f"shutil.which('npx.cmd'): {npx_cmd_path}")

if npx_cmd_path:
    try:
        result = subprocess.run(
            [npx_cmd_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(f"\nnpx works: {result.returncode == 0}")
        print(f"Version: {result.stdout.strip()}")
    except Exception as e:
        print(f"Error: {e}")
