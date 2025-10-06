from flask import Flask, request, render_template_string, jsonify
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estrattore Flussi TV Online</title>
    <style>
        body {
            background-color: #0f0f0f;
            color: #cfefff;
            font-family: 'Segoe UI', sans-serif;
            text-align: center;
            margin-top: 10%;
        }
        h1 { color: #40cfff; }
        p, h3 { color: #bdeaff; }
        input {
            padding: 10px;
            width: 50%;
            border-radius: 6px;
            border: none;
            background-color: #1b1b1b;
            color: #cfefff;
            margin-right: 10px;
        }
        input::placeholder {
            color: #7bcfff;
        }
        button {
            padding: 10px 20px;
            background-color: #40cfff;
            color: #0f0f0f;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover { background-color: #32aee0; }

        #loading-box {
            display: none;
            background-color: #1b1b1b;
            border-radius: 10px;
            padding: 30px;
            width: 320px;
            margin: 0 auto;
            margin-bottom: 25px;
            animation: fadein 0.3s ease-in;
            color: #bdeaff;
        }
        @keyframes fadein {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }
        .loader {
            border: 5px solid #333;
            border-top: 5px solid #40cfff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        #progress-bar {
            width: 100%;
            height: 8px;
            background-color: #333;
            border-radius: 4px;
            margin-top: 15px;
        }
        #progress {
            width: 0%;
            height: 8px;
            background-color: #40cfff;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        #result {
            margin-top: 25px;
            font-size: 16px;
        }
        ul {
            text-align: left;
            display: inline-block;
            color: #bdeaff;
        }
        a {
            color: #40cfff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .copy-btn {
            background-color: #1e88e5;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
            margin-left: 6px;
            cursor: pointer;
            font-size: 13px;
            transition: background 0.3s;
        }
        .copy-btn:hover {
            background-color: #1565c0;
        }
    </style>
</head>
<body>
    <div id="loading-box">
        <div class="loader"></div>
        <h3>Sto cercando il flusso...</h3>
        <p>Attendere qualche secondo ⏳</p>
        <div id="progress-bar"><div id="progress"></div></div>
    </div>

    <h1>🎬 Estrattore Flussi TV Online</h1>
    <p>Inserisci il link della diretta o della pagina video e premi <strong>Cerca flusso</strong>:</p>
    <input type="text" id="url" placeholder="https://esempio.com/diretta/tvcanale">
    <button onclick="cerca()">Cerca flusso</button>

    <div id="result"></div>

    <script>
        function cerca() {
            const url = document.getElementById('url').value;
            const resultDiv = document.getElementById('result');
            const loadingBox = document.getElementById('loading-box');
            const progress = document.getElementById('progress');
            resultDiv.innerHTML = "";
            loadingBox.style.display = "block";
            progress.style.width = "0%";

            let width = 0;
            const interval = setInterval(() => {
                if (width < 95) {
                    width += 2;
                    progress.style.width = width + "%";
                }
            }, 250);

            fetch(`/api?url=${encodeURIComponent(url)}`)
                .then(r => r.json())
                .then(data => {
                    clearInterval(interval);
                    progress.style.width = "100%";
                    setTimeout(() => { loadingBox.style.display = "none"; }, 500);

                    if (data.error) {
                        resultDiv.innerHTML = `<p style='color:#ff7777;'>❌ Errore: ${data.error}</p>`;
                    } else {
                        let output = "<p>✅ Flussi trovati:</p>";
                        output += "<ul>";
                        data.streams.forEach(s => {
                            output += `
                                <li>
                                    <a href='${s}' target='_blank'>${s}</a>
                                    <button class="copy-btn" onclick="copyToClipboard('${s}')">📋 Copia</button>
                                </li>`;
                        });
                        output += "</ul>";
                        resultDiv.innerHTML = output;
                    }
                })
                .catch(err => {
                    clearInterval(interval);
                    progress.style.width = "100%";
                    setTimeout(() => { loadingBox.style.display = "none"; }, 500);
                    resultDiv.innerHTML = `<p style='color:#ff7777;'>❌ Errore nella richiesta: ${err}</p>`;
                });
        }

        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                alert("✅ Flusso copiato negli appunti!");
            });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api")
def estrai_flusso():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Parametro 'url' mancante"}), 400

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage", "--no-sandbox"]
            )
            context = browser.new_context()
            page = context.new_page()

            flussi_trovati = []

            pattern = re.compile(
                r"("
                r"\.m3u8(\?|$)|"
                r"chunklist\.m3u8|"
                r"=hls|"
                r"aka_media_format_type=hls|"
                r"\.mpd(\?|$)|"
                r"manifest(_hr)?\.mpd|"
                r"dash/.+/master\.mpd"
                r")",
                re.IGNORECASE
            )

            def handle_request(request):
                if pattern.search(request.url) and request.url not in flussi_trovati:
                    flussi_trovati.append(request.url)

            page.on("request", handle_request)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=35000)
                page.wait_for_timeout(7000)
            except Exception as e:
                browser.close()
                return jsonify({"error": f"Errore di caricamento: {e}"}), 500

            browser.close()

            if flussi_trovati:
                return jsonify({"streams": flussi_trovati})
            return jsonify({"error": "Nessun flusso trovato"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
