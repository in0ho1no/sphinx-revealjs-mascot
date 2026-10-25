(() => {
    "use strict";

    const ACTIONS = {
        idle: { image: "normal" },
        jump: { image: "normal", duration: 600 },
        wink: { image: "blink", duration: 180 },
        surprise: { image: "surprise", duration: 700 },
        doze: { image: "sleepy" },
        wake: { image: "surprise", duration: 500 },
    };
    const BLINK = { min: 2200, max: 6000, duration: 140 };
    const MAX_TIMEOUT = 2147483647;

    function applyPosition(chara, config, slide) {
        const position = slide && slide.hasAttribute("data-mascot-position")
            ? {
                anchor: slide.getAttribute("data-mascot-position"),
                x: Number(slide.getAttribute("data-mascot-x")),
                y: Number(slide.getAttribute("data-mascot-y")),
                facing: Number(slide.getAttribute("data-mascot-facing")),
            }
            : config.position;

        chara.dataset.position = position.anchor;
        chara.style.setProperty("--mascot-x", `${position.x}vw`);
        chara.style.setProperty("--mascot-y", `${position.y}vh`);
        chara.style.setProperty("--mascot-facing", String(position.facing));
    }

    function showMascot(config) {
        if (document.getElementById("chara")) {
            return;
        }

        const chara = document.createElement("div");
        chara.id = "chara";
        chara.setAttribute("aria-hidden", "true");
        chara.style.setProperty("--mascot-width", `${config.width}vw`);

        let parent = chara;
        let reaction;
        for (const name of ["anchor", "sway", "breath", "react", "facing"]) {
            const layer = document.createElement("div");
            layer.className = name;
            parent.appendChild(layer);
            parent = layer;
            if (name === "react") reaction = layer;
        }

        const image = document.createElement("img");
        image.id = "chara-img";
        image.alt = "";
        image.draggable = false;
        const sprites = Object.fromEntries(Object.entries(config.images).map(([name, url]) => {
            const sprite = document.createElement("img");
            sprite.src = url;
            return [name, sprite];
        }));
        image.src = sprites.normal.src;
        parent.appendChild(image);
        const sleep = document.createElement("span");
        sleep.className = "mascot-sleep";
        sleep.textContent = "Zzz";
        reaction.appendChild(sleep);
        document.body.appendChild(chara);

        const deck = window.Reveal;
        const timers = new Map();
        let visible = true;
        let state = "idle";
        let lastActivity = performance.now();
        let previous = deck.getIndices(deck.getCurrentSlide());

        function cancel(name) {
            clearTimeout(timers.get(name));
            timers.delete(name);
        }

        function schedule(name, callback, delay) {
            cancel(name);
            const id = setTimeout(() => {
                if (!visible || timers.get(name) !== id) return;
                timers.delete(name);
                callback();
            }, delay);
            timers.set(name, id);
        }

        function scheduleBlink() {
            if (!visible || state !== "idle") return;
            schedule("blink", () => {
                image.src = sprites.blink.src;
                schedule("blinkEnd", () => {
                    image.src = sprites.normal.src;
                    scheduleBlink();
                }, BLINK.duration);
            }, BLINK.min + Math.random() * (BLINK.max - BLINK.min));
        }

        function runAction(action) {
            for (const name of ["blink", "blinkEnd", "reaction"]) cancel(name);
            state = action;
            const definition = ACTIONS[action];
            // 同じ CSS アニメーションも再実行するため、状態の代入だけでは済ませない。
            chara.dataset.state = "idle";
            void reaction.offsetWidth;
            chara.style.setProperty("--mascot-reaction-duration", `${definition.duration || 0}ms`);
            chara.dataset.state = action;
            image.src = sprites[definition.image].src;
            if (definition.duration) {
                schedule("reaction", () => runAction("idle"), definition.duration);
            } else if (action === "idle") {
                scheduleBlink();
            }
        }

        function resetIdleTimer() {
            lastActivity = performance.now();
            function check() {
                const remaining = config.idleTimeout * 1000 - (performance.now() - lastActivity);
                if (remaining > 0) {
                    schedule("idle", check, Math.min(remaining, MAX_TIMEOUT));
                } else {
                    runAction("doze");
                }
            }
            // 長い設定値でもブラウザのタイマー上限で直ちに発火しないよう分割する。
            schedule("idle", check, Math.min(config.idleTimeout * 1000, MAX_TIMEOUT));
        }

        function activity(action) {
            if (!visible) return;
            resetIdleTimer();
            if (state === "doze") {
                runAction("wake");
            } else if (action) {
                runAction(action);
            }
        }

        function resume() {
            previous = deck.getIndices(deck.getCurrentSlide());
            applyPosition(chara, config, deck.getCurrentSlide());
            runAction("idle");
            resetIdleTimer();
        }

        window.Reveal.on("slidechanged", (event) => {
            const current = deck.getIndices(event.currentSlide);
            const forward = current.h > previous.h || (current.h === previous.h && (current.v || 0) > (previous.v || 0));
            previous = current;
            if (visible) applyPosition(chara, config, event.currentSlide);
            activity(forward ? event.currentSlide.getAttribute("data-mascot-action") || config.defaultActions.slide : null);
        });
        deck.on("fragmentshown", (event) => {
            const fragment = event.fragments?.length ? event.fragments[event.fragments.length - 1] : event.fragment;
            activity(fragment.getAttribute("data-mascot-action") || config.defaultActions.fragment);
        });
        deck.on("fragmenthidden", () => activity(null));
        document.addEventListener("keydown", (event) => {
            if (event.defaultPrevented || event.isComposing || event.ctrlKey || event.altKey || event.metaKey) return;
            if (event.key.toLowerCase() !== config.toggleKey.toLowerCase()) return;
            if (event.target?.closest?.('input, textarea, select, [contenteditable]:not([contenteditable="false"])')) return;
            event.preventDefault();
            event.stopImmediatePropagation();
            if (event.repeat) return;
            visible = !visible;
            chara.hidden = !visible;
            if (visible) {
                resume();
            } else {
                for (const name of [...timers.keys()]) cancel(name);
                state = "idle";
                chara.dataset.state = state;
                image.src = sprites.normal.src;
            }
        }, { capture: true });
        resume();
    }

    function initialize() {
        const element = document.getElementById("sphinx-revealjs-mascot-config");
        if (!element || !window.Reveal) {
            return;
        }

        const config = JSON.parse(element.textContent);
        if (window.Reveal.isReady()) {
            showMascot(config);
        } else {
            window.Reveal.on("ready", () => showMascot(config));
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initialize, { once: true });
    } else {
        initialize();
    }
})();
