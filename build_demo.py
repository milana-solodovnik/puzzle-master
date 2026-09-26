# -*- coding: utf-8 -*-
"""Одноразовый сборщик статического демо puzzle-master для GitHub Pages.
Запускает Flask-приложение в тестовом клиенте, снимает отрендеренные страницы
для нового игрока, переписывает ссылки на относительные и складывает в demo/.
Реальная логика игры не меняется — страницы те же, данные живут в localStorage."""

import re
import sys
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

OUT = BASE / "demo"
OUT.mkdir(exist_ok=True)

# --- снимаем страницы через тестовый клиент Flask ---
from main import app, db, User, Achievement  # noqa: E402

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="demo_player").first():
        user = User(username="demo_player", password="demo_password")
        db.session.add(user)
        db.session.commit()
        db.session.add(Achievement(user=user))
        db.session.commit()

client = app.test_client()
resp = client.post("/login", data={"username": "demo_player", "password": "demo_password"})
assert resp.status_code == 302, f"login failed: {resp.status_code}"

pages = {
    "login.html": client.get("/login").get_data(as_text=True),
    "register.html": client.get("/register").get_data(as_text=True),
    "main_menu.html": client.get("/main_menu").get_data(as_text=True),
    "difficulty.html": client.get("/difficulty").get_data(as_text=True),
    "play.html": client.get("/play?difficulty=2x2").get_data(as_text=True),
    "achievements.html": client.get("/achievements").get_data(as_text=True),
}

STATIC_SRC = Path(__file__).parent / "static"
(OUT / "static").mkdir(exist_ok=True)
for f in STATIC_SRC.iterdir():
    (OUT / "static" / f.name).write_bytes(f.read_bytes())

# --- патчи страниц ---
def rewrite_links(html: str) -> str:
    html = html.replace('href="/main_menu"', 'href="main_menu.html"')
    html = html.replace('href="/difficulty"', 'href="difficulty.html"')
    html = html.replace('href="/achievements"', 'href="achievements.html"')
    html = html.replace('href="/logout"', 'href="index.html" data-demo="logout"')
    html = html.replace('href="/register"', 'href="register.html"')
    html = html.replace('href="/login"', 'href="index.html"')
    html = html.replace('href="/static/style.css"', 'href="static/style.css"')
    html = html.replace("`/play?difficulty=", "`play.html?difficulty=")
    html = html.replace('/play?difficulty=${difficulty}', 'play.html?difficulty=${difficulty}')
    html = html.replace('action="/login"', 'action="#" data-demo="login"')
    html = html.replace('action="/register"', 'action="#" data-demo="register"')
    html = html.replace('action="/delete_account"', 'action="#" data-demo="delete"')
    html = html.replace('"/puzzle_image/" + imageName', '"static/" + imageName + ".jpg"')
    html = html.replace('"/static/" + imageName + ".jpg"', '"static/" + imageName + ".jpg"')
    return html

# login/register: главная страница демо = index.html (копия login)
pages["index.html"] = pages["login.html"]

# main_menu: тестовое имя -> динамический span
pages["main_menu.html"] = pages["main_menu.html"].replace(
    "Добро пожаловать, demo_player!", 'Добро пожаловать, <span id="demo-username">…</span>!')

# play: сложность из URL, картинка из демо-прогресса
pages["play.html"] = pages["play.html"].replace(
    'const difficulty = "2x2";',
    'const difficulty = new URLSearchParams(location.search).get("difficulty") || "2x2";')
pages["play.html"] = pages["play.html"].replace(
    'const imageName = "puzzle1";',
    'const imageName = window.demoPickImage();')
# achievements: значения -> спаны, заполняемые из localStorage
pages["achievements.html"] = re.sub(
    r'<div class="achievement-status (incomplete|completed)">[^<]*</div>',
    lambda m, slots=iter(["first_puzzle", "five_puzzles", "speed_master"]):
        f'<div class="achievement-status incomplete" data-demo-ach="{next(slots)}">Не выполнено</div>',
    pages["achievements.html"])
pages["achievements.html"] = re.sub(
    r'<span>(Ещё не собран|\d+\.\d)</span>',
    lambda m, slots=iter(["2x2", "3x3", "4x4"]):
        f'<span data-demo-time="{next(slots)}">Ещё не собран</span>',
    pages["achievements.html"])

# подключаем demo-api.js в конец <head> каждой страницы
for name, html in pages.items():
    html = rewrite_links(html)
    html = html.replace("</head>", '  <script src="demo-api.js"></script>\n</head>')
    (OUT / name).write_text(html, encoding="utf-8")

print("pages:", sorted(pages.keys()))
print("done ->", OUT)
