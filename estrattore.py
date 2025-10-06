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
