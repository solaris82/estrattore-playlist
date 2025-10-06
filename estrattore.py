from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import re
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "<h2>Estrattore Playlist</h2><p>Usa /api?url=https://...</p>"

@app.route("/api")
def estrai_flusso():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing url"}), 400

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            page = browser.new_page()
            page.goto(url, timeout=60000)

            trovato = None
            for req in page.context.requests:
                if re.search(r"\.(m3u8|mpd)(\?|$)", req.url):
                    trovato = req.url
                    break

            browser.close()

            if trovato:
                return jsonify({"stream": trovato})
            return jsonify({"error": "No stream found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
