/**
 * Демо-режим puzzle-master для GitHub Pages.
 * Игра полностью клиентская; этот скрипт заменяет серверную часть:
 *  - регистрация/вход — в localStorage этого браузера (вместо БД);
 *  - /complete_puzzle — та же логика достижений, что в main.py + models.py;
 *  - выбор картинки пазла — из разблокированных в демо-прогрессе.
 * Реальный код игры не меняется.
 */

(function () {
  const STORE_KEY = "puzzle_demo_players";
  const SESSION_KEY = "puzzle_demo_session";

  function loadPlayers() {
    try { return JSON.parse(localStorage.getItem(STORE_KEY) || "{}"); }
    catch (e) { return {}; }
  }
  function savePlayers(players) {
    localStorage.setItem(STORE_KEY, JSON.stringify(players));
  }
  function currentPlayer() {
    const id = localStorage.getItem(SESSION_KEY);
    if (!id) return null;
    return loadPlayers()[id] || null;
  }
  function saveCurrent(player) {
    const players = loadPlayers();
    players[player.id] = player;
    savePlayers(players);
  }
  window.demoPickImage = function () {
    const p = currentPlayer();
    const images = (p && p.availableImages && p.availableImages.length) ? p.availableImages : ["puzzle1"];
    return images[Math.floor(Math.random() * images.length)];
  };

  // ---- CRUD "сервера" ----
  function registerPlayer(username, password) {
    const players = loadPlayers();
    if (Object.values(players).some(p => p.username === username)) {
      return { error: "Пользователь с таким именем уже существует" };
    }
    const nextId = parseInt(localStorage.getItem("puzzle_demo_next_id") || "1", 10);
    localStorage.setItem("puzzle_demo_next_id", String(nextId + 1));
    players[nextId] = {
      id: nextId,
      username: username,
      password: password,
      completedPuzzles: 0,
      bestTimes: {},
      achievements: {},
      availableImages: ["puzzle1"],
    };
    savePlayers(players);
    localStorage.setItem(SESSION_KEY, String(nextId));
    return { ok: true };
  }
  function loginUser(username, password) {
    const player = Object.values(loadPlayers()).find(p => p.username === username);
    if (!player) return { error: "Неверное имя пользователя или пароль" };
    if (player.password !== password) return { error: "Неверное имя пользователя или пароль" };
    localStorage.setItem(SESSION_KEY, String(player.id));
    return { ok: true };
  }

  function showFormError(form, message) {
    let box = form.querySelector(".demo-error");
    if (!box) {
      box = document.createElement("div");
      box.className = "demo-error";
      box.style.cssText = "color:#b23b3b;padding:6px 0;font-size:14px;";
      form.prepend(box);
    }
    box.textContent = message;
  }

  // ---- перехват /complete_puzzle ----
  const originalFetch = window.fetch.bind(window);
  window.fetch = async function (input, init) {
    const url = typeof input === "string" ? input : (input && input.url) || String(input);
    if (url.includes("/complete_puzzle")) {
      const player = currentPlayer();
      if (!player) {
        return new Response(JSON.stringify({ status: "error", message: "Не авторизован" }),
          { status: 200, headers: { "content-type": "application/json" } });
      }
      const data = JSON.parse((init && init.body) || "{}");
      const time = parseFloat(data.time);
      const difficulty = data.difficulty;
      const previousBest = player.bestTimes[difficulty] || null;
      const isNewRecord = previousBest === null || time < previousBest;
      if (isNewRecord) player.bestTimes[difficulty] = time;

      player.completedPuzzles += 1;
      if (player.completedPuzzles >= 1 && !player.achievements.first_puzzle) {
        player.achievements.first_puzzle = true;
        if (!player.availableImages.includes("puzzle2")) player.availableImages.push("puzzle2");
      }
      if (player.completedPuzzles >= 5 && !player.achievements.five_puzzles) {
        player.achievements.five_puzzles = true;
        if (!player.availableImages.includes("puzzle3")) player.availableImages.push("puzzle3");
        if (!player.availableImages.includes("puzzle4")) player.availableImages.push("puzzle4");
      }
      if (difficulty === "4x4" && time < 30 && !player.achievements.speed_master) {
        player.achievements.speed_master = true;
        if (!player.availableImages.includes("puzzle5")) player.availableImages.push("puzzle5");
      }
      saveCurrent(player);

      return new Response(JSON.stringify({
        status: "success",
        is_new_record: isNewRecord,
        previous_best: previousBest,
        achievements: player.achievements,
      }), { status: 200, headers: { "content-type": "application/json" } });
    }
    return originalFetch(input, init);
  };

  function hydrate() {
    const page = (location.pathname.split("/").pop() || "index.html").toLowerCase();

    // --- формы входа/регистрации ---
    const loginForm = document.querySelector('form[data-demo="login"]');
    if (loginForm) {
      loginForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const username = loginForm.querySelector('[name="username"]').value.trim();
        const password = loginForm.querySelector('[name="password"]').value;
        if (!username || !password) return showFormError(loginForm, "Пожалуйста, введите имя пользователя и пароль");
        const res = loginUser(username, password);
        if (res.error) return showFormError(loginForm, res.error);
        location.href = "main_menu.html";
      });
    }

    const registerForm = document.querySelector('form[data-demo="register"]');
    if (registerForm) {
      registerForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const username = registerForm.querySelector('[name="username"]').value.trim();
        const password = registerForm.querySelector('[name="password"]').value;
        if (!username || !password) return showFormError(registerForm, "Пожалуйста, введите имя пользователя и пароль");
        const res = registerPlayer(username, password);
        if (res.error) return showFormError(registerForm, res.error);
        location.href = "main_menu.html";
      });
    }

    // --- выход и удаление аккаунта ---
    document.querySelectorAll('a[data-demo="logout"]').forEach(a => {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        localStorage.removeItem(SESSION_KEY);
        location.href = "index.html";
      });
    });
    const deleteForm = document.querySelector('form[data-demo="delete"]');
    if (deleteForm) {
      deleteForm.addEventListener("submit", function (e) {
        e.preventDefault();
        if (!confirm("Удалить аккаунт? Это демо — удалятся только локальные данные.")) return;
        const id = localStorage.getItem(SESSION_KEY);
        const players = loadPlayers();
        if (id) { delete players[id]; savePlayers(players); }
        localStorage.removeItem(SESSION_KEY);
        location.href = "index.html";
      });
    }

    // --- имя игрока в меню ---
    const nameEl = document.getElementById("demo-username");
    if (nameEl) {
      const p = currentPlayer();
      nameEl.textContent = p ? p.username : "гость";
    }

    // --- страница достижений ---
    const achEls = document.querySelectorAll("[data-demo-ach]");
    if (achEls.length) {
      const p = currentPlayer() || { achievements: {}, bestTimes: {} };
      achEls.forEach(el => {
        const earned = !!(p.achievements || {})[el.getAttribute("data-demo-ach")];
        el.className = "achievement-status " + (earned ? "completed" : "incomplete");
        el.textContent = earned ? "Выполнено" : "Не выполнено";
      });
      document.querySelectorAll("[data-demo-time]").forEach(el => {
        const t = (p.bestTimes || {})[el.getAttribute("data-demo-time")];
        el.textContent = t ? (Math.round(t * 10) / 10 + " секунд") : "Ещё не собран";
      });
    }

    // --- защита страниц, требующих входа ---
    const guarded = ["main_menu.html", "difficulty.html", "play.html", "achievements.html"];
    if (guarded.some(g => page === g) && !currentPlayer()) {
      location.replace("index.html");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", hydrate);
  } else {
    hydrate();
  }
})();
