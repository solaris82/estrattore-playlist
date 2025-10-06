from flask import Flask, request, Response
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)

@app.route("/api")
def estrai_flusso():
    url = request.args.get("url")
    if not url:
        return Response("Missing url", status=400)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=60000)
        except Exception as e:
            browser.close()
            return Response(f"Cannot open {url}: {e}", status=500)

        trovato = None
        for req in page.context.requests:
            if re.search(r"\.m3u8(\?|$)", req.url) or re.search(r"\.mpd(\?|$)", req.url):
                trovato = req.url
                break

        browser.close()
        if trovato:
            return Response(trovato, status=200)
        return Response("No stream found", status=404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
