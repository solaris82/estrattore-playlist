from flask import Flask, request, render_template_string, jsonify
from playwright.sync_api import sync_playwright
import re
import subprocess
import os

app = Flask(__name__)

# --- HTML principale con form + modale di caricamento ---
PAGE_HTML = """
<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<title>Estrattore Playlist Online</title>
<style>
  body {
    font-family: "Segoe UI", sans-serif;
    background-color: #111;
    color: #eee;
    text-align: center;
    padding-top: 80px;
  }
  h2 { color: #4CAF50; }
  input[type=text] {
    width: 60%%;
    padding: 10px;
    border-radius: 8px;
    border: none;
    outline: none;
    font-size: 16px;
  }
  button {
    padding: 10px 20px;
    background: #4CAF50;
    border: none;
    color: white;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    margin-left: 10px;
  }
  button:hover { background: #45a049; }
  #result {
    margin-top: 40px;
    font-size: 18px;
  }
  a { color: #4CAF50; }

  /* --- MODALE --- */
  .modal {
    display: none;
    position: fixed;
    z-index: 10;
    left: 0; top: 0;
    width: 100%%; height: 100%%;
    background-color: rgba(0,0,0,0.7);
  }
  .modal-content {
    position: absolute;
    top: 50%%; left: 50%%;
    transform: translate(-50%%, -50%%);
    background-color: #222;
    padding: 30px;
    border-radius: 10px;
    width: 400px;
    color: white;
  }
  .spinner {
    border: 6px solid #333;
    border-top: 6px solid #4CAF50;
    border-radius: 50%%;
    width: 50px;
    height: 50px;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
  }
  @keyframes spin {
    0%% { transform: rotate(0deg); }
    100%% { transform: rotate(360deg); }
  }
  .progress {
    width: 100%%;
    height: 10px;
    background-color: #333;
    border-radius: 5px;
    overflow: hidden;
    margin-top: 15px;
  }
  .bar {
    height: 100%%;
    width: 0%%;
    background: linear-gradient(90deg, #00c853, #b2ff59);
  }
</style>
</head>
<body>
  <h2>🎬 Estrattore Playlist Online</h2>
  <p>Inserisci il link della diretta e premi <b>Cerca flusso</b>:</p>

  <input id="url" type="text" placeholder="https://www.raiplay.it/dirette/rai1">
  <button onclick="startSearch()">Cerca flusso</button>

  <div id="result"></div>

  <!-- Modale di caricamento -->
  <div id="loadingModal" class="modal">
    <div class="modal-content">
      <div class="spinner"></div>
      <h3>Sto cercando il flusso...</h3>
      <p>Attendere qualche secondo.</p>
      <div class="progress"><div class="bar" id="bar"></div></div>
    </div>
  </div>

<script>
function startSearch() {
  const url = document.getElementById("url").value.trim();
  const result = document.getElementById("result");
  const modal = document.getElementById("loadingModal");
  const bar = document.getElementById("bar");

  if (!url) {
    result.innerHTML = "<p style='color:red;'>⚠️ Inserisci un URL valido.</p>";
    return;
  }

  result.innerHTML = "";
  modal.style.display = "block";
  bar.style.width = "0%%";

  let width = 0;
  const interval = setInterval(() => {
    if (width >= 100) clearInterval(interval);
    else { width += 1; bar.style.width = width + "%%"; }
  }, 60);

  fetch(`/api?url=${encodeURIComponent(url)}`)
    .then(r => r.json())
    .then(data => {
      clearInterval(interval);
      bar.style.width = "100%%";
      setTimeout(() => { modal.style.display = "none"; }, 600);

      if (data.stream) {
        result.innerHTML = `
          <h3>✅ Flusso trovato!</h3>
          <p><a href="${data.stream}" target="_blank">${data.stream}</a></p>
        `;
      } else {
        result.innerHTML = "<h3>❌ Nessun flusso trovato.</h3>";
      }
    })
    .catch(err => {
      clearInterval(interval);
      modal.style.display = "none";
      result.innerHTML = "<p style='color:red;'>Errore durante la ricerca.</p>";
      console.error(err);
    });
}
</script>
</body>
</html>
"""

# --- ROUTES BACKEND ---
@app.route("/")
def home():
    return render_template_string(PAGE_HTML)

@app.route("/api")
def estrai_flusso():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing url"}), 400

    browsers_path = "/opt/render/.cache/ms-playwright"
    chromium_executable = f"{browsers_path}/chromium_headless_shell-1187/chrome-linux/headless_shell"

    # Installa Chromium se manca
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
            page.goto(url, timeout=90000)
            browser.close()

            if trovato["url"]:
                return jsonify({"stream": trovato["url"]})
            else:
                return jsonify({"error": "No stream found"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
