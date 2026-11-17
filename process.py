"""Download product photos listed in urls.csv and save them as square JPEGs
(white padding, never cropped) into img/<id>.jpg."""
import csv, io, sys, time
from pathlib import Path
import requests
from PIL import Image

MAX_SIDE = 1000
PAD = 1.06  # 3% white margin on each side
out = Path("img"); out.mkdir(exist_ok=True)
headers = {"User-Agent": "Mozilla/5.0 (compatible; feed-image-builder)"}
failed = []

for row in csv.DictReader(open("urls.csv", encoding="utf-8")):
    pid, url = row["id"].strip(), row["url"].strip()
    dest = out / f"{pid}.jpg"
    if dest.exists():
        continue
    try:
        r = None
        for attempt in range(3):
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                break
            time.sleep(2)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content))
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
            bg.alpha_composite(im)
            im = bg
        im = im.convert("RGB")
        side = int(max(im.size) * PAD)
        canvas = Image.new("RGB", (side, side), (255, 255, 255))
        canvas.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
        if side > MAX_SIDE:
            canvas = canvas.resize((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        canvas.save(dest, "JPEG", quality=90, optimize=True)
        print("ok", pid, im.size, "->", canvas.size)
    except Exception as e:
        print("FAIL", pid, url, e)
        failed.append(pid)

print(f"done, failed={len(failed)}")
if failed:
    sys.exit(1)
# trigger build
