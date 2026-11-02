import getpass
import json
import sys

from src.auth import TEACHERS_FILE, hash_password, load_teachers


def main() -> int:
    username = sys.argv[1].strip() if len(sys.argv) > 1 else input("Teacher username: ").strip()
    if not username or "\n" in username:
        print("A valid username is required.", file=sys.stderr)
        return 1

    teachers = load_teachers()
    if username in teachers:
        print(f"Teacher '{username}' already exists.", file=sys.stderr)
        return 1

    password = getpass.getpass("Teacher password (12+ characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if len(password) < 12:
        print("Password must be at least 12 characters.", file=sys.stderr)
        return 1
    if password != confirmation:
        print("Passwords do not match.", file=sys.stderr)
        return 1

    teachers[username] = hash_password(password)
    TEACHERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEACHERS_FILE.write_text(json.dumps(teachers, indent=2) + "\n", encoding="utf-8")
    print(f"Added teacher '{username}' to {TEACHERS_FILE}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())