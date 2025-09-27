from pathlib import Path

def transform_line(line: str) -> str:
    return line.rstrip().upper()

def read_and_write(src_path: Path, dst_path: Path) -> None:
    with src_path.open("r", encoding="utf-8") as src, dst_path.open("w", encoding="utf-8") as dst:
        for i, line in enumerate(src, start=1):
            dst.write(f"LINE {i}: {transform_line(line)}\n")

if __name__ == "__main__":
    src_name = input("Enter source filename (e.g., notes.txt): ").strip()
    src = Path(src_name)
    out = src.with_name(f"modified_{src.name}")
    read_and_write(src, out)
    print(f"Done! Wrote: {out}")
