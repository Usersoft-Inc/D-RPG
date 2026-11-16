(() => {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const esc = (s) => String(s).replace(/[&<>]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[ch]);
  const t = (text, cls) => (cls ? `<span class="${cls}">${esc(text)}</span>` : esc(text));
  const center = (s, w) => " ".repeat(Math.max(0, Math.floor((w - s.length) / 2))) + s;
  const bar = (cur, max, width, cls) => {
    const filled = Math.round((width * Math.max(0, cur)) / max);
    return "[" + t("#".repeat(filled), cls) + t("-".repeat(width - filled), "c-grey") + "]";
  };
  const menu = (opts) => opts.map(([k, v]) => t(`[${k}]`, "c-byellow") + " " + v).join("   ");

  const HERO_ART = [
    "               __",
    "              / _)",
    "     _.----._/ /",
    "    /         /",
    " __/ (  | (  |",
    "/__.-'|_|--|_|",
  ];

  // ---------------------------------------------------------- главное меню

  const LETTERS = {
    D: [" ____  ", "|  _ \\ ", "| | | |", "| |_| |", "|____/ "],
    "-": ["       ", "       ", " _____ ", "|_____|", "       "],
    R: [" ____  ", "|  _ \\ ", "| |_) |", "|  _ < ", "|_| \\_\\"],
    E: [" _____ ", "| ____|", "|  _|  ", "| |___ ", "|_____|"],
    X: ["__  __", "\\ \\/ /", " \\  / ", " /  \\ ", "/_/\\_\\"],
  };
  const W = 79;
  const top = ["", ""];
  for (let row = 0; row < 5; row++) {
    const line = [..."D-REX"].map((ch) => LETTERS[ch][row]).join("  ");
    top.push(t(center(line, W).trimEnd(), "c-hero"));
  }
  top.push("", t(center("Д О Л Б А З А В Р    R P G", W).trimEnd(), "c-byellow"));
  document.getElementById("title-top").innerHTML = top.join("\n");
  document.getElementById("dino-art").textContent = HERO_ART.join("\n");
  document.getElementById("title-foot").textContent = center("v1.0.0  (c) Долбазавр Студиос, Usersoft Inc. 2026-2028", W).trimEnd();

  const screen = document.getElementById("title-screen");
  const bye = document.getElementById("bye");
  const titleParts = [...screen.children].filter((el) => el !== bye);

  function showBye() {
    titleParts.forEach((el) => (el.hidden = true));
    bye.hidden = false;
    bye.innerHTML = "\n" + t("  Пока! Не вымирайте.", "c-byellow") + "\n\n" +
      t("  …шутка. Долбазавр никуда не уйдёт.", "c-grey") + "\n\n  " +
      '<button type="button" class="back">' + t("[Enter]", "c-byellow") + " Вернуться в меню</button>";
    const back = bye.querySelector(".back");
    back.addEventListener("click", hideBye);
    back.focus({ preventScroll: true });
  }
  function hideBye() {
    bye.hidden = true;
    titleParts.forEach((el) => (el.hidden = false));
    screen.querySelector('[data-key="3"]').focus({ preventScroll: true });
  }

  function choose(key) {
    if (key === "1") {
      document.getElementById("story").scrollIntoView();
      playStory(true);
    } else if (key === "2") {
      document.getElementById("download").scrollIntoView();
    } else if (key === "3") {
      showBye();
    }
  }
  document.getElementById("title-menu").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-key]");
    if (b) choose(b.dataset.key);
  });

  let heroVisible = true;
  new IntersectionObserver(([en]) => (heroVisible = en.isIntersecting), { threshold: 0.4 })
    .observe(document.getElementById("title-term"));
  document.addEventListener("keydown", (e) => {
    if (!heroVisible || e.ctrlKey || e.altKey || e.metaKey) return;
    if (!bye.hidden) {
      if (e.key === "Enter" || e.key === "Escape") { e.preventDefault(); hideBye(); }
      return;
    }
    if (["1", "2", "3"].includes(e.key)) choose(e.key);
  });

  const dino = document.getElementById("dino");
  const roar = document.getElementById("roar");
  const ROARS = ["БУМ!", "Р-Р-Р!", "ДОЛБО-УДАР!", "Ой. Лоб.", "Ещё!", "Где метеор?"];
  let bonks = 0;
  dino.addEventListener("click", () => {
    roar.textContent = ROARS[bonks++ % ROARS.length];
    if (reduceMotion) return;
    dino.classList.remove("bonk");
    void dino.offsetWidth;
    dino.classList.add("bonk");
  });

  // ---------------------------------------------------------------- сюжет

  const STORY = [
    ["Давным-давно, в эпоху, когда папоротники были большими...", "c-white", 20],
    ["...с неба рухнул МЕТЕОР ПОГИБЕЛИ.", "c-bred", 20],
    ["Он упал в Вулканическом краю, и из трещин полезла всякая нечисть.", "c-white", 20],
    ["Все умные динозавры сразу спрятались.", "c-white", 20],
    ["Но Долбазавр не был умным.", "c-hero", 20],
    ["Долбазавр был ДОЛБАЗАВРОМ.", "c-hero", 40],
  ];
  const storyEl = document.getElementById("story-text");
  const storyDone = STORY.map(([s, cls]) => "  " + t(s, cls)).join("\n") +
    "\n\n  " + t("Нажмите любую клавишу...", "c-grey") + '<span class="cursor"></span>';
  let storyRun = 0;
  let storyStarted = false;

  function playStory(restart) {
    if (storyStarted && !restart) return;
    storyStarted = true;
    const run = ++storyRun;
    if (reduceMotion) { storyEl.innerHTML = storyDone; return; }
    let li = 0, ci = 0, html = "";
    const tick = () => {
      if (run !== storyRun) return;
      if (li >= STORY.length) { storyEl.innerHTML = storyDone; return; }
      const [s, cls, delay] = STORY[li];
      ci++;
      storyEl.innerHTML = html + "  " + t(s.slice(0, ci), cls) + '<span class="cursor"></span>';
      if (ci >= s.length) {
        html += "  " + t(s, cls) + "\n";
        li++; ci = 0;
        setTimeout(tick, 350);
      } else {
        setTimeout(tick, delay);
      }
    };
    tick();
  }
  storyEl.innerHTML = '  <span class="cursor"></span>';
  new IntersectionObserver(([en], obs) => {
    if (en.isIntersecting) { playStory(false); obs.disconnect(); }
  }, { threshold: 0.5 }).observe(storyEl);

  // ----------------------------------------------------------------- карта

  const MAP = [
    "############################################",
    "#^^^^......TTTTT.......~~~~......TTTT..^^^^#",
    "#^^.......TTTTTT..?....~~~~.....TTTTTT.^^B^#",
    "#^....H....TTTT........~~~~.......TTTT..^.^#",
    "#......................~~~~.......?.....^.^#",
    "#......TT..............~~~~...^^^.......^.^#",
    "#.....TTTT.......TTTT..~~~~..^^^^^.........#",
    "#....TTTTTT..?....TT...~~~~...^^^...TTTT...#",
    "#.....TTTT.............====.......TTTTTTTT.#",
    "#......TT.......~~~....~~~~.......TTTT..?..#",
    "#..............~~~~~...~~~~..............TT#",
    "#...?....TT.....~~~....~~~~...TT...^^.....T#",
    "#.......TTTT...........~~~~..TTTT.^^^^.....#",
    "#^^.....TT.......TTT...~~~~...TT...^^....^^#",
    "#^^^^...........TTTTT..~~~~..?.........^^^^#",
    "############################################",
  ];
  const TILES = {
    ".": "c-green", T: "c-bgreen", "~": "c-bblue", "^": "c-white", H: "c-byellow",
    "?": "c-bmagenta", B: "c-boss", "=": "c-yellow", "#": "c-grey",
  };
  const hero = { x: 8, y: 5, lvl: 3, hp: 52, maxHp: 74, xp: 40, xpNext: 180 };
  const panel = [
    t(`ДОЛБАЗАВР  Ур. ${hero.lvl}`, "c-hero"),
    `HP  ${bar(hero.hp, hero.maxHp, 12, "c-bgreen")} ${hero.hp}/${hero.maxHp}`,
    `XP  ${bar(hero.xp, hero.xpNext, 12, "c-bcyan")} ${hero.xp}/${hero.xpNext}`,
    "Атака: 18   Защита: 8",
    `Золото: ${t("63", "c-byellow")}   Зелья: ${t("3", "c-bgreen")}`,
    "Оружие: Костяная дубина",
    "Броня:  Шкура мамонта",
    "",
    `Местность: ${t("Папоротниковые луга", "c-bgreen")}`,
    `Опасность: ${t("*", "c-bgreen")}`,
    "",
    t("Легенда:", "c-grey"),
    `${t("@", "c-hero")} вы   ${t("H", "c-byellow")} деревня  ${t("?", "c-bmagenta")} сундук`,
    `${t("T", "c-bgreen")} лес  ${t("~", "c-bblue")} вода     ${t("^", "c-white")} горы`,
    `${t("=", "c-yellow")} мост ${t("B", "c-boss")} ЛОГОВО МЕТЕОРА`,
    "",
  ];
  const mapLines = [""];
  MAP.forEach((row, y) => {
    let out = "", cur = null, buf = "";
    const flush = () => { if (buf) out += t(buf, cur); buf = ""; };
    [...row].forEach((ch, x) => {
      const [cls, sym] = x === hero.x && y === hero.y ? ["c-hero", "@"] : [TILES[ch], ch];
      if (cls !== cur) { flush(); cur = cls; }
      buf += sym;
    });
    flush();
    mapLines.push("  " + out + "   " + (panel[y] || ""));
  });
  mapLines.push("", "  " + t("Вы выходите из деревни. Пахнет серой и приключениями.", "c-bwhite"), "",
    "  " + menu([["WASD/стрелки", "идти"], ["I", "герой"], ["H", "помощь"], ["Q", "выход"]]));
  document.getElementById("map-screen").innerHTML = mapLines.join("\n");

  // ------------------------------------------------------------------- бой

  const METEOR = [
    "            .  *   .      *",
    "       *   _.-\"\"\"\"-._   .",
    "     .   .'  .   .   '.     *",
    "        /  ( O )  ( O ) \\",
    "   *   |    .  ____  .   |",
    "       |   .  /VVVV\\    .| *",
    "        \\     \\^^^^/    /",
    "    *    '.  .  .  .  .'   .",
    "   ~~~~~~~~`-.______.-'~~~~~~",
    "  ~~~ ~~~~ ~~~ ~~~~~ ~~ ~~~ ~~",
  ];
  const p = { name: "ДОЛБАЗАВР", lvl: 7, hp: 81, maxHp: 122, rage: 55 };
  const e = { hp: 231, maxHp: 420 };
  const b = [""];
  b.push("  " + t(p.name, "c-hero") + `  Ур.${p.lvl}` +
    " ".repeat(40 - p.name.length - String(p.lvl).length - 7) + t("МЕТЕОР ПОГИБЕЛИ", "c-boss"));
  b.push(`  HP     ${bar(p.hp, p.maxHp, 14, "c-bgreen")} ${String(p.hp).padStart(3)}/${String(p.maxHp).padEnd(4)}` +
    `       HP ${bar(e.hp, e.maxHp, 14, "c-bred")} ${e.hp}/${e.maxHp}`);
  b.push(`  Ярость ${bar(p.rage, 100, 14, "c-byellow")} ${String(p.rage).padStart(3)}`, "");
  const h = Math.max(HERO_ART.length, METEOR.length);
  const heroCol = Array(h - HERO_ART.length).fill("").concat(HERO_ART);
  for (let i = 0; i < h; i++) {
    const mid = i === h - 3 ? t("  VS  ", "c-bwhite") : "      ";
    b.push("  " + t(heroCol[i].padEnd(20), "c-bgreen") + mid + t(METEOR[i], "c-boss"));
  }
  const rule = "  " + t("-".repeat(66), "c-grey");
  b.push("", rule,
    "  Вы кусаете МЕТЕОР ПОГИБЕЛИ на " + t("27", "c-bwhite") + " урона.",
    "  " + t("Метеор раскаляется добела... Сейчас рванёт! (защищайтесь!)", "c-bred"),
    "  " + t("Вы прячете голову и упираетесь хвостом.", "c-bcyan"),
    "  " + t("МЕТЕОР ПОГИБЕЛИ: ОГНЕННЫЙ ДОЖДЬ! 31 урона (вы защитились)!", "c-boss"),
    "  " + t("ДОЛБО-УДАР!!! Вы бьёте лбом со всей дури: 96 урона!", "c-byellow"),
    rule,
    "  " + menu([["1", "Атака"], ["2", "Долбо-удар"], ["3", "Защита"], ["4", "Зелье x2"]]));
  document.getElementById("battle-screen").innerHTML = b.join("\n");
})();
