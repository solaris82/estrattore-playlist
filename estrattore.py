from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h2>✅ Estrattore Playlist Online</h2>
    <p>Usa: <code>/api?url=https://...</code></p>
    <p>Esempio: <a href="/api?url=https://www.raiplay.it/dirette/rai1">/api?url=https://www.raiplay.it/dirette/rai1</a></p>
    """

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
                return jsonify({"stream_url": trovato}), 200
            return jsonify({"message": "No stream found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
