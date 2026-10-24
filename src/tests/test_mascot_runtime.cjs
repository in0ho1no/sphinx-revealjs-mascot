"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

const source = fs.readFileSync(
    path.join(__dirname, "../sphinx_revealjs_mascot/static/sphinx-revealjs-mascot/mascot.js"),
    "utf8",
);

function fixture({ ready = true, loading = false, initialSlide = null } = {}) {
    const elements = new Map();
    const listeners = new Map();
    const domListeners = new Map();
    function element() {
        return {
            children: [],
            dataset: {},
            attributes: new Map(),
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
        images: { normal: "_static/images/normal.png" },
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
        getCurrentSlide: () => initialSlide,
        on: (name, handler) => listeners.set(name, handler),
    };
    const context = vm.createContext({ document, window: { Reveal } });
    vm.runInContext(source, context);
    return { document, listeners, domListeners, elements, context };
}

function slide(position) {
    const attrs = position ? {
        "data-mascot-position": position.anchor,
        "data-mascot-x": String(position.x),
        "data-mascot-y": String(position.y),
        "data-mascot-facing": String(position.facing),
    } : {};
    return {
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
