from flask import Flask, request, Response
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h2>✅ Estrattore Playlist Online</h2>
    <p>Usa: <code>/api?url=https://...</code></p>
    <p>Esempio: <a href="/api?url=https://www.raiplay.it/dirette/rai1" target="_blank">
    /api?url=https://www.raiplay.it/dirette/rai1</a></p>
    <p>Funziona con flussi .m3u8 e .mpd</p>
    """

@app.route("/api")
def estrai_flusso():
    url = request.args.get("url")
    if not url:
        return Response('{"error":"Missing url"}', status=400, mimetype="application/json")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)

            trovato = None
            for req in page.context.requests:
                if re.search(r"\.m3u8(\?|$)", req.url) or re.search(r"\.mpd(\?|$)", req.url):
                    trovato = req.url
                    break

            browser.close()

            if trovato:
                return Response(f'{{"stream":"{trovato}"}}', mimetype="application/json")
            else:
                return Response('{"error":"No stream found"}', status=404, mimetype="application/json")

    except Exception as e:
        return Response(f'{{"error":"{str(e)}"}}', status=500, mimetype="application/json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
