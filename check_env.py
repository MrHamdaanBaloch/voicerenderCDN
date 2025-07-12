import os
import shutil
import subprocess
from dotenv import load_dotenv

# --- Style ---
class style:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

def print_check(name, status, message=""):
    status_text = f"{style.GREEN}OK{style.RESET}" if status else f"{style.RED}FAIL{style.RESET}"
    print(f"[{status_text}] {name.ljust(30)} {message}")

def check_ffmpeg():
    """Checks if ffmpeg is installed and in the system's PATH."""
    print(f"\n--- Checking for Dependencies ---")
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
            version_line = result.stdout.splitlines()[0]
            print_check("ffmpeg installation", True, f"Found at: {ffmpeg_path}")
            print(f"      {style.YELLOW}Version: {version_line}{style.RESET}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_check("ffmpeg installation", False, "Found but could not execute 'ffmpeg -version'.")
            return False
    else:
        print_check("ffmpeg installation", False, "ffmpeg not found in system PATH.")
        print(f"      {style.YELLOW}Please install ffmpeg and ensure it's in your PATH.{style.RESET}")
        return False

def check_env_vars():
    """Checks for required environment variables."""
    print(f"\n--- Checking for Environment Variables ---")
    load_dotenv()
    
    required_vars = [
        "SIGNALWIRE_PROJECT_ID",
        "SIGNALWIRE_API_TOKEN",
        "SIGNALWIRE_CONTEXT",
        "GROQ_API_KEY",
        "PUBLIC_URL_BASE"
    ]
    
    all_found = True
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print_check(var, True)
        else:
            print_check(var, False, "Not found in .env file or environment.")
            all_found = False
            
    return all_found

def main():
    print("\n=== Environment Sanity Check ===")
    ffmpeg_ok = check_ffmpeg()
    env_ok = check_env_vars()
    
    print("\n--- Summary ---")
    if ffmpeg_ok and env_ok:
        print(f"{style.GREEN}All checks passed! Your environment is ready.{style.RESET}")
    else:
        print(f"{style.RED}Some checks failed. Please review the output above and fix the issues before proceeding.{style.RESET}")
    print("\n")

if __name__ == "__main__":
    main()
