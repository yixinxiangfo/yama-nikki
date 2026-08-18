#!/usr/bin/env python3
"""
koutei-log.html の「JSONで書き出す」で出力したバックアップファイルを受け取り、
写真を「日付_時刻_地点名.jpg」の個別ファイルに展開し、テキストログも書き出す。

使い方:
    python3 extract_koutei_log.py ~/Downloads/koutei-log-backup-2026-08-18.json
    (引数を省略すると ~/Downloads の中で一番新しい koutei-log-backup-*.json を自動で探す)

出力先: このスクリプトと同じ階層の extracted/<日付>/ 以下
"""

import base64
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = SCRIPT_DIR / "extracted"


def find_latest_backup():
    downloads = Path.home() / "Downloads"
    candidates = sorted(downloads.glob("koutei-log-backup-*.json"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        return None
    return candidates[-1]


def sanitize(name: str) -> str:
    name = name.strip() or "無題"
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    return name


def save_photo(data_url: str, dest_path: Path):
    header, _, b64data = data_url.partition(",")
    ext = "jpg"
    if "png" in header:
        ext = "png"
    dest_path = dest_path.with_suffix(f".{ext}")
    dest_path.write_bytes(base64.b64decode(b64data))
    return dest_path


def main():
    if len(sys.argv) > 1:
        src = Path(sys.argv[1]).expanduser()
    else:
        src = find_latest_backup()
        if src is None:
            print("~/Downloads に koutei-log-backup-*.json が見つかりませんでした。")
            print("引数でファイルパスを直接指定してください。")
            sys.exit(1)
        print(f"自動検出: {src}")

    if not src.exists():
        print(f"ファイルが見つかりません: {src}")
        sys.exit(1)

    data = json.loads(src.read_text(encoding="utf-8"))

    total_photos = 0
    for date, entries in sorted(data.items()):
        day_dir = OUTPUT_ROOT / date
        day_dir.mkdir(parents=True, exist_ok=True)

        text_lines = [f"## {date}", ""]
        for entry in sorted(entries, key=lambda e: e.get("time", "")):
            time = entry.get("time", "----")
            place = entry.get("place", "")
            memo = entry.get("memo", "")

            line = f"{place}{time}"
            if memo:
                line += f"　{memo}"
            text_lines.append(line)

            photos = entry.get("photos") or []
            for i, data_url in enumerate(photos, start=1):
                base_name = f"{date}_{time.replace(':', '')}_{sanitize(place)}"
                if len(photos) > 1:
                    base_name += f"_{i}"
                dest = day_dir / base_name
                saved = save_photo(data_url, dest)
                total_photos += 1
                print(f"  写真: {saved.name}")

        text_path = day_dir / f"{date}_log.txt"
        text_path.write_text("\n".join(text_lines), encoding="utf-8")
        print(f"テキストログ: {text_path}")

    print(f"\n完了。写真 {total_photos} 枚を展開しました。出力先: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
