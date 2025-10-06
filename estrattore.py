from flask import Flask, request, jsonify, render_template_string
from playwright.sync_api import sync_playwright
import re
import subprocess
import os
import time

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

    # ✅ Mostra messaggio "Sto cercando..." prima di processare
    loading_html = f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="2">
        <style>
            body {{ font-family: sans-serif; text-align: center; margin-top: 100px; }}
            h2 {{ color: #4CAF50; }}
        </style>
    </head>
    <body>
        <h2>⏳ Sto cercando il flusso per:</h2>
        <p>{url}</p>
        <p>Attendere qualche secondo...</p>
    </body>
    </html>
    """
    # Mostra subito l'HTML di caricamento (Render lo visualizza in streaming)
    print("🟢 Ricerca flusso in corso per:", url, flush=True)

    browsers_path = "/opt/render/.cache/ms-playwright"
    chromium_executable = f"{browsers_path}/chromium_headless_shell-1187/chrome-linux/headless_shell"

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
                    "--disable-http2",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--ignore-certificate-errors",
                    "--disable-features=IsolateOrigins,site-per-process",
                ]
            )
            page = browser.new_page()

            trovato = {"url": None}

            def handle_request(req):
                if re.search(r"\.(m3u8|mpd)(\?|$)", req.url):
                    trovato["url"] = req.url

            page.on("request", handle_request)

            print("🌐 Navigazione verso:", url, flush=True)
            page.goto(url, timeout=90000)

            browser.close()

            if trovato["url"]:
                return render_template_string(f"""
                    <h2>✅ Flusso trovato!</h2>
                    <p><b>URL:</b> <a href='{trovato["url"]}' target='_blank'>{trovato["url"]}</a></p>
                """)
            else:
                return render_template_string("""
                    <h2>❌ Nessun flusso trovato</h2>
                    <p>Prova con un altro link o controlla la pagina sorgente.</p>
                """)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
