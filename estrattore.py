from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import re
import subprocess
import os

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h2>✅ Estrattore Playlist Online</h2>
    <p>Usa: <code>/api?url=https://...</code></p>
    <p>Esempio: 
        <a href='/api?url=https://www.raiplay.it/dirette/rai1'>
        /api?url=https://www.raiplay.it/dirette/rai1</a>
    </p>
    <p>Funziona con flussi .m3u8 e .mpd</p>
    """

@app.route("/api")
def estrai_flusso():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing url"}), 400

    browsers_path = "/opt/render/.cache/ms-playwright"
    chromium_executable = f"{browsers_path}/chromium_headless_shell-1187/chrome-linux/headless_shell"

    # ✅ Installa Chromium se non esiste (Render spesso lo cancella)
    if not os.path.exists(chromium_executable):
        try:
            os.makedirs(browsers_path, exist_ok=True)
            subprocess.run(
                ["python", "-m", "playwright", "install", "chromium"],
                env={**os.environ, "PLAYWRIGHT_BROWSERS_PATH": browsers_path},
                check=True,
            )
        except Exception as e:
            return jsonify({"error": f"Failed to install Chromium: {e}"}), 500

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-http2",  # ✅ Fix per RaiPlay
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--ignore-certificate-errors",
                    "--disable-features=IsolateOrigins,site-per-process",
                ]
            )
            page = browser.new_page()

            # Timeout maggiore per siti lenti come RaiPlay
            page.goto(url, timeout=90000)

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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
