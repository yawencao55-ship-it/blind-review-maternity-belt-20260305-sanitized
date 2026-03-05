from pathlib import Path

import re


def main() -> None:
    p = Path("../data/input/paper_final.md")
    t = p.read_text(encoding="utf-8")
    lines = t.splitlines()

    open_count = t.count('<span style="color:blue">')
    close_count = t.count("</span>")

    print(f"[OK] span open: {open_count}")
    print(f"[OK] span close: {close_count}")

    nested = t.count('<span style="color:blue"><span style="color:blue">')
    print(f"[OK] nested-blue-span count: {nested}")

    if nested:
        nested_pat = '<span style="color:blue"><span style="color:blue">'
        print("[INFO] nested-blue-span occurrences:")
        for idx, line in enumerate(lines, 1):
            if nested_pat in line:
                safe = line.encode("utf-8", "backslashreplace").decode("ascii", "ignore")
                print(f"  line {idx}: {safe}")

    # Check citation number range
    nums: set[int] = set()
    for m in re.finditer(r"\[(\d+(?:\s*,\s*\d+)*)\]", t):
        for x in re.split(r"\s*,\s*", m.group(1)):
            if x.isdigit():
                nums.add(int(x))

    if nums:
        print(f"[OK] citation min: {min(nums)}")
        print(f"[OK] citation max: {max(nums)}")
        print(f"[OK] citation unique: {len(nums)}")
    else:
        print("[WARN] no citations found")

    # Count reference entries
    marker = "## References"
    if marker in t:
        after = t.split(marker, 1)[1]
        cut_idx = after.find("---")
        if cut_idx != -1:
            refs_block = after[:cut_idx]
            refs_block = re.sub(r"<span[^>]*>", "", refs_block).replace("</span>", "").strip()
            refs = [r.strip() for r in re.split(r"\n\s*\n", refs_block) if r.strip()]
            print(f"[OK] refs count: {len(refs)}")
        else:
            print("[WARN] could not locate end of References section")
    else:
        print("[WARN] References section not found")

    # Quick check around References section
    marker = "## References"
    if marker in t:
        after = t.split(marker, 1)[1]
        # limit window
        window = after[:6000]
        open_refs = window.count('<span style="color:blue">')
        close_refs = window.count("</span>")
        print(f"[OK] references-window span open: {open_refs}")
        print(f"[OK] references-window span close: {close_refs}")


if __name__ == "__main__":
    main()

