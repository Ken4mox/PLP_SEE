from pathlib import Path

def preview_file(path: Path) -> None:
    with path.open("r", encoding="utf-8") as f:
        content = f.read()
        print("\n--- File Preview (first 200 chars) ---")
        print(content[:200])
        print("--------------------------------------")

if __name__ == "__main__":
    name = input("Enter a filename to read: ").strip()
    p = Path(name)

    try:
        if not p.exists():
            raise FileNotFoundError(f"'{p}' does not exist.")
        if p.is_dir():
            raise IsADirectoryError(f"'{p}' is a directory, not a file.")
        preview_file(p)

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except PermissionError:
        print("Error: You don't have permission to read this file.")
    except IsADirectoryError as e:
        print(f"Error: {e}")
    except UnicodeDecodeError:
        print("Error: Could not decode file (try a different encoding).")
    except OSError as e:
        print(f"OS Error: {e}")
    else:
        print("File read successfully ✅")
    finally:
        print("Operation complete.")
