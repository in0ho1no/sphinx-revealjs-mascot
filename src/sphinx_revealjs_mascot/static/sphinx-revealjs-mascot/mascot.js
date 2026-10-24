(() => {
    "use strict";

    function showMascot(config) {
        if (document.getElementById("chara")) {
            return;
        }

        const chara = document.createElement("div");
        chara.id = "chara";
        chara.setAttribute("aria-hidden", "true");
        chara.style.setProperty("--mascot-width", `${config.width}vw`);

        let parent = chara;
        for (const name of ["anchor", "sway", "breath", "react", "facing"]) {
            const layer = document.createElement("div");
            layer.className = name;
            parent.appendChild(layer);
            parent = layer;
        }

        const image = document.createElement("img");
        image.id = "chara-img";
        image.alt = "";
        image.draggable = false;
        image.src = config.images.normal;
        parent.appendChild(image);
        document.body.appendChild(chara);
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
