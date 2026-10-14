"""Браузер нұсқасын нақты Chromium-да тексеру (GitHub Actions ішінде).

Іске қосу: python tools/web_smoke.py build/web [секунд]
Сайтты ашады, «бастау» үшін бетті басады, біраз күтеді, скриншот алады және
экранда ойын мәзірінің түстері бар-жоғын тексереді. Консоль журналын (FPS, қателер) басып шығарады.
"""
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

root = Path(sys.argv[1]).resolve()
wait_s = int(sys.argv[2]) if len(sys.argv) > 2 else 60
out = Path("web-smoke.png")

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", 8000), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

logs = []
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required",
                                      "--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    page.on("console", lambda m: logs.append(m.text))
    page.on("pageerror", lambda e: logs.append("PAGEERROR " + str(e)))
    page.goto("http://127.0.0.1:8000/index.html")
    waited = 0
    while waited < wait_s:                       # pygbag: «Ready to start! Please click» — дайын болғанша басу
        page.wait_for_timeout(10000)
        waited += 10
        page.mouse.click(640, 360)
        if any(l.startswith("FPS ") for l in logs):
            break
    page.wait_for_timeout(8000)                  # біраз ойнатып, содан кейін скриншот
    page.screenshot(path=str(out))
    browser.close()
print(f"waited {waited}s")

img = Image.open(out).convert("RGB")
w, h = img.size
px = img.load()
total = w * h
bright = sum(1 for y in range(0, h, 4) for x in range(0, w, 4) if sum(px[x, y]) > 120) * 16
red = sum(1 for y in range(0, h, 2) for x in range(0, w, 2)
          if abs(px[x, y][0] - 200) < 40 and abs(px[x, y][1] - 60) < 40 and abs(px[x, y][2] - 60) < 40) * 4
print(f"screenshot {w}x{h}: bright={bright / total:.3f} accent_red_px={red}")
print("--- console (last 60) ---")
for line in logs[-60:]:
    print(line[:220])
fps = [l for l in logs if l.startswith("FPS ")]
print("FPS lines:", fps[-5:])
errors = [l for l in logs if "Traceback" in l or l.startswith("PAGEERROR")]
print("errors:", errors[:5])
ok = bool(fps) and red > 50          # нақты ойын кадрлары: FPS журналы және мәзірдің қызыл белгісі
print("WEB SMOKE", "OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
