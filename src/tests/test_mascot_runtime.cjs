"use strict";

const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

const repository = path.resolve(__dirname, "../..");
const contract = JSON.parse(execFileSync("uv", [
    "--cache-dir", path.join(repository, ".uv_cache"), "run", "--frozen", "--no-sync", "--offline",
    "python", "-X", "utf8", "-c", [
        "import sys; sys.path.insert(0, 'src')",
        "import json",
        "from dataclasses import asdict",
        "from sphinx_revealjs_mascot.config import ACTIONS, DEFAULT_ACTIONS, STATES",
        "from sphinx_revealjs_mascot.directives import _EXPLICIT_ACTIONS",
        "print(json.dumps({'actions': {name: asdict(value) for name, value in ACTIONS.items()}, 'defaults': DEFAULT_ACTIONS, 'states': STATES, 'explicit': _EXPLICIT_ACTIONS}))",
    ].join("\n"),
], { cwd: repository, encoding: "utf8" }));

const source = fs.readFileSync(
    path.join(__dirname, "../sphinx_revealjs_mascot/static/sphinx-revealjs-mascot/mascot.js"),
    "utf8",
);

function fakeClock() {
    let now = 0;
    let nextId = 1;
    const pending = new Map();
    return {
        pending,
        now: () => now,
        setTimeout(callback, delay) {
            assert.ok(delay >= 0 && delay <= 2147483647);
            const id = nextId++;
            pending.set(id, { callback, time: now + delay });
            return id;
        },
        clearTimeout(id) { pending.delete(id); },
        next() {
            return [...pending.entries()].sort((a, b) => a[1].time - b[1].time || a[0] - b[0])[0];
        },
        advance(duration) {
            const end = now + duration;
            let job;
            while ((job = this.next()) && job[1].time <= end) {
                pending.delete(job[0]);
                now = job[1].time;
                job[1].callback();
            }
            now = end;
        },
        advanceNext() {
            const next = this.next();
            assert.ok(next, "タイマーが登録されていること");
            this.advance(next[1].time - now);
        },
    };
}

function fixture({ ready = true, loading = false, initialSlide = null, overrides = {} } = {}) {
    const elements = new Map();
    const listeners = new Map();
    const domListeners = new Map();
    const clock = fakeClock();
    let currentSlide = initialSlide;
    let restarts = 0;
    function element() {
        return {
            children: [],
            dataset: {},
            attributes: new Map(),
            hidden: false,
            get offsetWidth() { restarts++; return 100; },
            style: {
                setProperty(name, value) {
                    this[name] = value;
                },
            },
            setAttribute(name, value) {
                this.attributes.set(name, value);
            },
            appendChild(child) {
                this.children.push(child);
                if (child.id) elements.set(child.id, child);
            },
        };
    }
    const config = {
        width: 12.5,
        position: { anchor: "bottom-right", x: 100, y: 100, facing: -1 },
        images: Object.fromEntries(contract.states.map((state) => [state, `_static/images/${state}.png`])),
        idleTimeout: 10,
        toggleKey: "x",
        defaultActions: contract.defaults,
        actions: contract.actions,
        ...overrides,
    };
    elements.set("sphinx-revealjs-mascot-config", { textContent: JSON.stringify(config) });
    const document = {
        readyState: loading ? "loading" : "complete",
        body: element(),
        createElement: element,
        getElementById: (id) => elements.get(id) || null,
        addEventListener: (name, handler) => domListeners.set(name, handler),
    };
    const Reveal = {
        isReady: () => ready,
        getCurrentSlide: () => currentSlide,
        getIndices: (target) => target?.indices || { h: 0, v: 0 },
        on: (name, handler) => listeners.set(name, handler),
    };
    const math = Object.create(Math);
    math.random = () => 0.5;
    const context = vm.createContext({
        document, window: { Reveal }, Math: math,
        setTimeout: clock.setTimeout.bind(clock), clearTimeout: clock.clearTimeout.bind(clock),
        performance: { now: clock.now },
    });
    vm.runInContext(source, context);
    return {
        document, listeners, domListeners, elements, context, clock,
        restarts: () => restarts,
        emit(name, event = {}) {
            if (name === "slidechanged") currentSlide = event.currentSlide;
            listeners.get(name)(event);
        },
        key(key = config.toggleKey, options = {}) {
            let prevented = false;
            let stopped = false;
            const event = {
                key,
                preventDefault() { prevented = true; },
                stopImmediatePropagation() { stopped = true; },
                ...options,
            };
            domListeners.get("keydown")(event);
            return { prevented, stopped };
        },
    };
}

function slide(position, { h = 0, v = 0, action = null } = {}) {
    const attrs = position ? {
        "data-mascot-position": position.anchor,
        "data-mascot-x": String(position.x),
        "data-mascot-y": String(position.y),
        "data-mascot-facing": String(position.facing),
    } : {};
    if (action) attrs["data-mascot-action"] = action;
    return {
        indices: { h, v },
        hasAttribute: (name) => Object.hasOwn(attrs, name),
        getAttribute: (name) => attrs[name] ?? null,
    };
}

test("DOM と reveal.js の準備完了を待ち、重複生成しない", () => {
    const state = fixture({ ready: false, loading: true });
    assert.equal(state.document.body.children.length, 0);
    state.domListeners.get("DOMContentLoaded")();
    assert.equal(state.document.body.children.length, 0);
    state.listeners.get("ready")();
    assert.equal(state.document.body.children.length, 1);
    state.listeners.get("ready")();
    assert.equal(state.document.body.children.length, 1);
});

test("初期スライドの位置と向きを適用する", () => {
    const state = fixture({ initialSlide: slide({ anchor: "top-left", x: 0, y: 0, facing: 1 }) });
    const chara = state.elements.get("chara");
    assert.equal(chara.dataset.position, "top-left");
    assert.equal(chara.style["--mascot-facing"], "1");
    assert.equal(state.elements.get("chara-img").src, "_static/images/normal.png");
});

test("位置指定から既定位置へ戻り、戻る操作でも移動先の値を使う", () => {
    const state = fixture();
    const chara = state.elements.get("chara");
    const move = state.listeners.get("slidechanged");
    const left = slide({ anchor: "bottom-left", x: 0, y: 100, facing: 1 });
    move({ currentSlide: left });
    assert.equal(chara.dataset.position, "bottom-left");
    assert.equal(chara.style["--mascot-facing"], "1");
    move({ currentSlide: slide(null) });
    assert.equal(chara.dataset.position, "bottom-right");
    assert.equal(chara.style["--mascot-facing"], "-1");
    move({ currentSlide: left });
    assert.equal(chara.dataset.position, "bottom-left");
    assert.equal(chara.style["--mascot-facing"], "1");
});

test("任意座標と中央での元画像の向きを適用する", () => {
    const state = fixture();
    const chara = state.elements.get("chara");
    state.listeners.get("slidechanged")({ currentSlide: slide({ anchor: "center", x: 50, y: 40, facing: 1 }) });
    assert.equal(chara.dataset.position, "center");
    assert.equal(chara.style["--mascot-x"], "50vw");
    assert.equal(chara.style["--mascot-y"], "40vh");
    assert.equal(chara.style["--mascot-facing"], "1");
});

function currentState(state) {
    return state.elements.get("chara").dataset.state;
}

function currentImage(state) {
    return state.elements.get("chara-img").src;
}

test("初期表示は指定アクションを実行せず idle で始まる", () => {
    const state = fixture({ initialSlide: slide(null, { action: "surprise" }) });
    assert.equal(currentState(state), "idle");
    assert.match(currentImage(state), /normal\.png$/);
});

test("idle 中にまばたきし、通常画像へ戻る", () => {
    const state = fixture();
    state.clock.advanceNext();
    assert.equal(currentState(state), "idle");
    assert.match(currentImage(state), /blink\.png$/);
    state.clock.advanceNext();
    assert.match(currentImage(state), /normal\.png$/);
});

test("まばたきを中断したリアクションへ古い復帰処理が割り込まない", () => {
    const state = fixture();
    state.clock.advanceNext();
    state.emit("fragmentshown", { fragment: slide(null, { action: "surprise" }) });
    state.clock.advance(200);
    assert.equal(currentState(state), "surprise");
    assert.match(currentImage(state), /surprise\.png$/);
    state.clock.advance(800);
    assert.equal(currentState(state), "idle");
    assert.match(currentImage(state), /normal\.png$/);
});

test("前進は jump、fragment 表示は wink を既定アクションにする", () => {
    const state = fixture();
    state.emit("slidechanged", { currentSlide: slide(null, { h: 1 }) });
    assert.equal(currentState(state), "jump");
    state.clock.advance(1000);
    assert.equal(currentState(state), "idle");
    state.emit("fragmentshown", { fragment: slide(null) });
    assert.equal(currentState(state), "wink");
    assert.match(currentImage(state), /blink\.png$/);
    state.clock.advance(1000);
    assert.equal(currentState(state), "idle");
});

test("スライド順は水平・垂直の両方で比較し、戻る操作ではアクションを始めない", () => {
    const state = fixture({ initialSlide: slide(null, { h: 1, v: 1 }) });
    state.emit("slidechanged", { currentSlide: slide(null, { h: 1, v: 2, action: "surprise" }) });
    assert.equal(currentState(state), "surprise");
    state.clock.advance(1000);
    state.emit("slidechanged", { currentSlide: slide(null, { h: 2, v: 0 }) });
    assert.equal(currentState(state), "jump");
    state.clock.advance(1000);
    state.emit("slidechanged", { currentSlide: slide(null, { h: 1, v: 3, action: "surprise" }) });
    assert.equal(currentState(state), "idle");
    state.emit("slidechanged", { currentSlide: slide(null, { h: 1, v: 2, action: "surprise" }) });
    assert.equal(currentState(state), "idle");
});

test("最新の指定でリアクションと完了タイマーを置き換える", () => {
    const state = fixture();
    state.emit("slidechanged", { currentSlide: slide(null, { h: 1 }) });
    const obsoleteCompletion = state.clock.next()[1].callback;
    state.clock.advance(100);
    state.emit("fragmentshown", { fragment: slide(null, { action: "surprise" }) });
    obsoleteCompletion();
    state.clock.advance(550);
    assert.equal(currentState(state), "surprise");
    state.clock.advance(200);
    assert.equal(currentState(state), "idle");
});

test("同じアクションでもアニメーションと完了待ちを最初からやり直す", () => {
    const state = fixture();
    state.emit("fragmentshown", { fragment: slide(null, { action: "jump" }) });
    const previousRestarts = state.restarts();
    state.clock.advance(400);
    state.emit("fragmentshown", { fragment: slide(null, { action: "jump" }) });
    assert.equal(state.restarts(), previousRestarts + 1);
    state.clock.advance(250);
    assert.equal(currentState(state), "jump");
    state.clock.advance(400);
    assert.equal(currentState(state), "idle");
});

test("明示した idle は既定アクションを実行せず進行中のリアクションを取り消す", () => {
    const state = fixture();
    state.emit("fragmentshown", { fragment: slide(null, { action: "surprise" }) });
    state.emit("slidechanged", { currentSlide: slide(null, { h: 1, action: "idle" }) });
    assert.equal(currentState(state), "idle");
    assert.match(currentImage(state), /normal\.png$/);
});

test("リアクション完了後はまばたきの待ち時間を数え直す", () => {
    const state = fixture();
    state.clock.advance(4000);
    state.emit("fragmentshown", { fragment: slide(null, { action: "jump" }) });
    state.clock.advance(1000);
    assert.match(currentImage(state), /normal\.png$/);
    state.clock.advanceNext();
    assert.match(currentImage(state), /blink\.png$/);
});

test("無操作で doze になり、まばたきと有限リアクションのタイマーを止める", () => {
    const state = fixture();
    state.clock.advance(10000);
    assert.equal(currentState(state), "doze");
    assert.match(currentImage(state), /sleepy\.png$/);
    assert.equal(state.clock.pending.size, 0);
    state.clock.advance(30000);
    assert.equal(currentState(state), "doze");
});

test("マウス移動とスライドが変わらないキー入力は無操作時間をリセットしない", () => {
    const state = fixture();
    state.clock.advance(9000);
    state.key("a");
    state.domListeners.get("mousemove")?.({});
    state.clock.advance(1000);
    assert.equal(currentState(state), "doze");
});

test("戻る操作と fragment の非表示も無操作タイマーをリセットする", () => {
    const state = fixture({ initialSlide: slide(null, { h: 2 }) });
    state.clock.advance(9000);
    state.emit("slidechanged", { currentSlide: slide(null, { h: 1, action: "surprise" }) });
    state.clock.advance(9000);
    assert.equal(currentState(state), "idle");
    state.emit("fragmenthidden");
    state.clock.advance(9000);
    assert.equal(currentState(state), "idle");
    state.clock.advance(1000);
    assert.equal(currentState(state), "doze");
});

test("戻る操作と fragment の非表示は進行中のリアクションを中断しない", () => {
    const state = fixture({ initialSlide: slide(null, { h: 2 }) });
    state.emit("fragmentshown", { fragment: slide(null, { action: "surprise" }) });
    const restarts = state.restarts();
    state.emit("slidechanged", { currentSlide: slide(null, { h: 1, action: "jump" }) });
    state.emit("fragmenthidden");
    assert.equal(state.restarts(), restarts);
    assert.equal(currentState(state), "surprise");
});

for (const event of ["slidechanged", "fragmentshown", "fragmenthidden"]) {
    test(`doze 中の ${event} は指定より wake を優先する`, () => {
        const state = fixture({ initialSlide: slide(null, { h: 2 }) });
        state.clock.advance(10000);
        state.emit(event, {
            currentSlide: slide(null, { h: 1, action: "jump" }),
            fragment: slide(null, { action: "idle" }),
        });
        assert.equal(currentState(state), "wake");
        assert.match(currentImage(state), /surprise\.png$/);
        state.clock.advance(1000);
        assert.equal(currentState(state), "idle");
    });
}

test("wake 中でも新しいアクションへ切り替え、古い完了処理を取り消す", () => {
    const state = fixture();
    state.clock.advance(10000);
    state.emit("fragmenthidden");
    state.clock.advance(100);
    state.emit("fragmentshown", { fragment: slide(null, { action: "jump" }) });
    state.clock.advance(450);
    assert.equal(currentState(state), "jump");
    state.clock.advance(300);
    assert.equal(currentState(state), "idle");
});

test("同時表示された fragment は最後の指定を採用し、doze なら wake だけ実行する", () => {
    const state = fixture();
    const fragments = [slide(null, { action: "jump" }), slide(null, { action: "surprise" })];
    state.emit("fragmentshown", { fragment: fragments[0], fragments });
    assert.equal(currentState(state), "surprise");
    state.clock.advance(10000);
    state.emit("fragmentshown", { fragment: fragments[0], fragments });
    assert.equal(currentState(state), "wake");
});

test("非表示中はタイマーを止め、イベントを蓄積しない", () => {
    const state = fixture();
    const chara = state.elements.get("chara");
    state.emit("fragmentshown", { fragment: slide(null, { action: "surprise" }) });
    assert.deepEqual(state.key(), { prevented: true, stopped: true });
    assert.equal(chara.hidden, true);
    assert.equal(state.clock.pending.size, 0);
    const left = slide({ anchor: "bottom-left", x: 0, y: 100, facing: 1 }, { h: 4, action: "jump" });
    state.emit("slidechanged", { currentSlide: left });
    state.emit("fragmentshown", { fragment: slide(null) });
    state.emit("fragmenthidden");
    state.clock.advance(60000);
    assert.equal(state.clock.pending.size, 0);
    state.key();
    assert.equal(chara.hidden, false);
    assert.equal(chara.dataset.position, "bottom-left");
    assert.equal(chara.style["--mascot-facing"], "1");
    assert.equal(currentState(state), "idle");
    state.clock.advance(9000);
    assert.equal(currentState(state), "idle");
    state.clock.advance(1000);
    assert.equal(currentState(state), "doze");
});

test("ウトウト中に非表示にしても再表示は wake を挟まず idle から始める", () => {
    const state = fixture();
    state.clock.advance(10000);
    state.key();
    state.key();
    assert.equal(currentState(state), "idle");
    assert.match(currentImage(state), /normal\.png$/);
});

test("表示切り替えは設定キーだけを処理し、修飾キー・入力欄・IME を妨げない", () => {
    const state = fixture();
    const chara = state.elements.get("chara");
    for (const options of [
        { ctrlKey: true }, { altKey: true }, { metaKey: true }, { isComposing: true },
        { defaultPrevented: true }, { target: { closest: () => ({}) } },
    ]) {
        assert.deepEqual(state.key("x", options), { prevented: false, stopped: false });
        assert.equal(chara.hidden, false);
    }
    assert.deepEqual(state.key("m"), { prevented: false, stopped: false });
    state.key("x", { repeat: true });
    assert.equal(chara.hidden, false);
    state.key("X", { shiftKey: true });
    assert.equal(chara.hidden, true);
});

test("Zzz は画像の左右反転要素の外側に置く", () => {
    const state = fixture();
    let layer = state.elements.get("chara");
    for (let i = 0; i < 4; i++) layer = layer.children[0];
    assert.equal(layer.className, "react");
    assert.equal(layer.children[0].className, "facing");
    assert.equal(layer.children[0].children.length, 1);
    assert.equal(layer.children[1].textContent, "Zzz");
});

test("ブラウザの上限を超える無操作時間を安全なタイマー長へ分割する", () => {
    const state = fixture({ overrides: { idleTimeout: 1e20 } });
    assert.equal(currentState(state), "idle");
    assert.ok([...state.clock.pending.values()].some((job) => job.time === 2147483647));
});

test("Python のアクション定義と明示指定・既定アクション・CSS の状態名が一致する", () => {
    const names = Object.keys(contract.actions);
    assert.deepEqual(contract.explicit, names.filter((name) => contract.actions[name].explicit));
    for (const name of Object.values(contract.defaults)) {
        assert.ok(contract.explicit.includes(name));
    }
    for (const [name, definition] of Object.entries(contract.actions)) {
        assert.ok(contract.states.includes(definition.image), name);
        assert.ok(Number.isFinite(definition.duration) && definition.duration >= 0, name);
    }
    const css = fs.readFileSync(path.join(repository, "src/sphinx_revealjs_mascot/static/sphinx-revealjs-mascot/mascot.css"), "utf8");
    const cssStates = [...new Set([...css.matchAll(/\[data-state="([^"]+)"\]/g)].map((match) => match[1]))].sort();
    assert.deepEqual(cssStates, names.filter((name) => contract.actions[name].motion).sort());
    for (const action of contract.explicit) {
        const state = fixture();
        state.emit("fragmentshown", { fragment: slide(null, { action }) });
        assert.equal(currentState(state), action);
        assert.equal(currentImage(state), `_static/images/${contract.actions[action].image}.png`);
    }
});

test("不正なアクションでも待機中のまばたきタイマーを壊さない", () => {
    const state = fixture();
    const blinkTimer = state.clock.next()[0];
    for (const action of ["unknown", "constructor", "__proto__"]) {
        state.emit("fragmentshown", { fragment: slide(null, { action }) });
        assert.equal(currentState(state), "idle");
        assert.equal(state.clock.next()[0], blinkTimer);
    }
    state.clock.advanceNext();
    assert.match(currentImage(state), /blink\.png$/);
    state.clock.advanceNext();
    assert.match(currentImage(state), /normal\.png$/);
});

test("不正なアクションが来ても進行中のリアクションと完了処理を継続する", () => {
    const state = fixture();
    state.emit("fragmentshown", { fragment: slide(null, { action: "surprise" }) });
    const completion = state.clock.next()[0];
    state.emit("fragmentshown", { fragment: slide(null, { action: "unknown" }) });
    assert.equal(currentState(state), "surprise");
    assert.equal(state.clock.next()[0], completion);
    state.clock.advance(1000);
    assert.equal(currentState(state), "idle");
});
