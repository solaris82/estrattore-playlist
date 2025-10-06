from flask import Flask, request, render_template_string, jsonify
from playwright.sync_api import sync_playwright
import re
import subprocess
import os
import threading

app = Flask(__name__)

# HTML principale con form, barra di caricamento e area risultati
PAGE_HTML = """
<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<title>Estrattore Playlist Online</title>
<style>
  body {
    font-family: Arial, sans-serif;
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
  .progress {
    width: 80%%;
    height: 25px;
    background-color: #333;
    border-radius: 15px;
    margin: 40px auto 20px;
    overflow: hidden;
    display: none;
  }
  .bar {
    height: 100%
