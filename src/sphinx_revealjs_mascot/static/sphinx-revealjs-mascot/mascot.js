(() => {
    "use strict";

    const BLINK = { min: 2200, max: 6000, duration: 140 };
    const MAX_TIMEOUT = 2147483647;

    function motionGaps(width, height, label, motion, actions) {
        const sine = (angle) => Math.sin(angle * Math.PI / 180);
        let horizontal = 0;
        let top = 0;
        let bottom = 0;
        for (const [action, scale, angle, lift, shift] of [
            ["idle", 1, 0, 0, 0],
            ["jump", 1, 0, motion.jump_height, 0],
            ["surprise", motion.surprise_scale, 0, 0, 0],
            ["happy", 1, motion.happy_angle, motion.happy_height, 0],
            ["tilt", 1, motion.tilt_angle, 0, 0],
            ["trouble", 1, 0, 0, motion.trouble_shift],
            ["proud", motion.proud_scale, 0, 0, 0],
            ["wake", 1, motion.wake_angle, motion.wake_height, 0],
            ["doze", 1, motion.doze_max_angle, 0, 0],
        ]) {
            // 画像のない追加アクションは実行されないため、その変位で表示幅や余白を狭めない。
            if (!Object.hasOwn(actions, action)) continue;
            const stretch = scale * motion.breath_scale;
            const tilt = sine(angle + motion.sway_angle);
            // 横移動は外側の揺れで回転するため、横だけでなく上下にも変位を生む。
            const shifted = stretch * shift * width;
            horizontal = Math.max(horizontal, (stretch - 1) * width / 2 + stretch * height * tilt + lift * height * stretch * sine(motion.sway_angle) + shifted);
            top = Math.max(top, (stretch - 1) * height + stretch * width / 2 * tilt + lift * height * stretch + shifted * sine(motion.sway_angle));
            bottom = Math.max(bottom, stretch * width / 2 * tilt + shifted * sine(motion.sway_angle));
        }
        // 透明部分を差し引かず、画像全体と Zzz の矩形を保守的に画面内へ収める。
        const tilt = sine(motion.doze_max_angle + motion.sway_angle);
        const textRight = width * (0.5 - motion.sleep_right);
        const textX = Math.max(Math.abs(textRight - label.width), Math.abs(textRight));
        const textUp = height + label.height * motion.sleep_rise;
        const textDown = Math.max(0, label.height - height);
        horizontal = Math.max(horizontal, motion.breath_scale * (textX + Math.max(textUp, textDown) * tilt) - width / 2);
        top = Math.max(top, motion.breath_scale * (textUp + textX * tilt) - height);
        bottom = Math.max(bottom, motion.breath_scale * (textDown + textX * tilt));
        return {
            horizontal: Math.ceil(horizontal + motion.edge_gap),
            top: Math.ceil(top + motion.edge_gap),
            bottom: Math.ceil(bottom + motion.edge_gap),
        };
    }

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
        chara.dataset.ready = "false";
        chara.style.setProperty("--mascot-width", `${config.width}vw`);
        for (const [name, value] of Object.entries(config.motion)) {
            const unit = name.endsWith("_angle") ? "deg" : name.endsWith("_duration") ? "ms" : "";
            chara.style.setProperty(`--mascot-${name.replaceAll("_", "-")}`, `${value}${unit}`);
        }

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

        function layout() {
            if (!visible || !image.naturalWidth || !image.naturalHeight) return;
            const ratio = image.naturalHeight / image.naturalWidth;
            const label = { width: sleep.offsetWidth, height: sleep.offsetHeight };
            const requested = window.innerWidth * config.width / 100;
            function fits(width) {
                const gaps = motionGaps(width, width * ratio, label, config.motion, config.actions);
                return width + 2 * gaps.horizontal <= window.innerWidth && width * ratio + gaps.top + gaps.bottom <= window.innerHeight;
            }
            let width = requested;
            if (!fits(width)) {
                let low = 0;
                let high = requested;
                for (let i = 0; i < 40; i++) {
                    const middle = (low + high) / 2;
                    if (fits(middle)) low = middle;
                    else high = middle;
                }
                width = Math.floor(low * 1000) / 1000;
            }
            const gaps = motionGaps(width, width * ratio, label, config.motion, config.actions);
            chara.style.setProperty("--mascot-rendered-width", `${width}px`);
            chara.style.setProperty("--mascot-horizontal-gap", `${gaps.horizontal}px`);
            chara.style.setProperty("--mascot-top-gap", `${gaps.top}px`);
            chara.style.setProperty("--mascot-bottom-gap", `${gaps.bottom}px`);
            chara.dataset.ready = "true";
        }

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
            if (!Object.hasOwn(config.actions, action)) return;
            const definition = config.actions[action];
            for (const name of ["blink", "blinkEnd", "reaction"]) cancel(name);
            state = action;
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
            layout();
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
        image.addEventListener("load", layout);
        window.addEventListener("resize", layout);
        resume();

        // 画像の読み込みと配置が終わるまでは CSS で隠れているため、受け付けたリアクションが見えないまま終わる。
        const shown = () => visible && chara.dataset.ready === "true";
        window.RevealMascot = Object.freeze({
            getAvailableActions: () => Object.keys(config.actions).filter((name) => config.actions[name].explicit),
            trigger(action) {
                // 不正な指定で無操作タイマーやウトウトからの復帰を動かさないよう、受け付ける前に除外する。
                if (!shown() || typeof action !== "string" || !Object.hasOwn(config.actions, action) || !config.actions[action].explicit) return;
                activity(action);
            },
            isVisible: shown,
        });
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
