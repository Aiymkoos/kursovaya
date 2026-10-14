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
    page.wait_for_timeout(25000)
    page.mouse.click(640, 360)                 # pygbag: «Ready to start! Please click» 
    page.wait_for_timeout(wait_s * 1000)
    page.screenshot(path=str(out))
    browser.close()

img = Image.open(out).convert("RGB")
w, h = img.size
px = img.load()
total = w * h
bright = sum(1 for y in range(0, h, 4) for x in range(0, w, 4) if sum(px[x, y]) > 120) * 16
red = sum(1 for y in range(0, h, 2) for x in range(0, w, 2)
          if abs(px[x, y][0] - 200) < 40 and abs(px[x, y][1] - 60) < 40 and abs(px[x, y][2] - 60) < 40) * 4
print(f"screenshot {w}x{h}: bright={bright / total:.3f} accent_red_px={red}")
print("--- console (последние 40) ---")
for line in logs[-40:]:
    print(line[:200])
fps = [l for l in logs if l.startswith("FPS ")]
print("FPS lines:", fps[-5:])
ok = bright / total > 0.01
print("WEB SMOKE", "OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
