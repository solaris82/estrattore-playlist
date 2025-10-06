from flask import Flask, request, render_template_string, jsonify
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)

# === HTML Template con animazione ===
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Estrattore Playlist Online</title>
    <style>
        body {
            background-color: #0f0f0f;
            color: #f1f1f1;
            font-family: 'Segoe UI', sans-serif;
            text-align: center;
            margin-top: 10%;
        }
        h1 { color: #3ccf57; }
        input {
            padding: 10px;
            width: 50%;
            border-radius: 6px;
            border: none;
            margin-right: 10px;
        }
        button {
            padding: 10px 20px;
            background-color: #3ccf57;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }
        button:hover { background-color: #2fa746; }

        #loading-box {
            display: none;
            background-color: #1b1b1b;
            border-radius: 10px;
            padding: 30px;
            width: 320px;
            margin: 0 auto;
            margin-bottom: 25px;
            animation: fadein 0.3s ease-in;
        }
        @keyframes fadein {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }
        .loader {
            border: 5px solid #333;
            border-top: 5px solid #3ccf57;
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
            background-color: #444;
            border-radius: 4px;
            margin-top: 15px;
        }
        #progress {
            width: 0%;
            height: 8px;
            background-color: #3ccf57;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        #result {
            margin-top: 25px;
            font-size: 16px;
        }
        a {
            color: #3ccf57;
            word-break: break-all;
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

    <h1>🎬 Estrattore Playlist Online</h1>
    <p>Inserisci il link della diretta e premi <strong>Cerca flusso</strong>:</p>
    <input type="text" id="url" placeholder="https://www.raiplay.it/dirette/rai1">
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
                        resultDiv.innerHTML = `<p style='color:red;'>❌ Errore: ${data.error}</p>`;
                    } else {
                        resultDiv.innerHTML = `<p>✅ Flusso trovato:</p><a href='${data.stream}' target='_blank'>${data.stream}</a>`;
                    }
                })
                .catch(err => {
                    clearInterval(interval);
                    progress.style.width = "100%";
                    setTimeout(() => { loadingBox.style.display = "none"; }, 500);
                    resultDiv.innerHTML = `<p style='color:red;'>❌ Errore nella richiesta: ${err}</p>`;
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
def estrai_flus_
