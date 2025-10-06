from flask import Flask, request, Response
from playwright.sync_api import sync_playwright
import re
import os

app = Flask(__name__)

@app.route("/api")
def estrai_flusso():
    url = request.args.get("url")
    if not url:
        return Response("Missing url parameter (?url=...)", status=400)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(url, timeout=60000)
        except Exception as e:
            browser.close()
            return Response(f"Cannot open {url}: {e}", status=500)

        trovato = None
        # Analizza le richieste per trovare stream .m3u8 o .mpd
        for req in page.context.requests:
            if re.search(r"\.m3u8(\?|$)", req.url) or re.search(r"\.mpd(\?|$)", req.url):
                trovato = req.url
                break

        browser.close()

        if trovato:
            return Response(trovato, status=200, mimetype="text/plain")
        else:
            return Response("No stream found", status=404)

# Avvio server: Render assegna una porta automatica
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
