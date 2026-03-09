import subprocess
import sys

def main():
    try:
        result = subprocess.run(
            [sys.executable, "live_verification.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        with open("live_verif_full_log.txt", "w", encoding="utf-8") as f:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)
        print("Log generated.")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    main()
