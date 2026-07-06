// Progressive Enhancement für das Upload-Formular.
// Ohne JS funktioniert der Upload weiterhin (klassischer Datei-Dialog + Submit).
(function () {
    "use strict";

    const dropzone = document.querySelector("[data-dropzone]");
    if (!dropzone) return;

    const input = dropzone.querySelector('input[type="file"]');
    const list = document.querySelector("[data-filelist]");
    const submit = document.querySelector("[data-submit]");

    function isHtml(name) {
        return /\.html?$/i.test(name);
    }

    function render(files) {
        const html = [...files].filter((f) => isHtml(f.name));
        list.innerHTML = "";
        for (const f of html) {
            const li = document.createElement("li");
            li.textContent = f.name;
            list.appendChild(li);
        }
        const skipped = files.length - html.length;
        if (skipped > 0) {
            const li = document.createElement("li");
            li.style.opacity = "0.6";
            li.textContent = `${skipped} Nicht-HTML-Datei(en) werden ignoriert`;
            list.appendChild(li);
        }
        if (submit) {
            submit.disabled = html.length === 0;
            submit.textContent = html.length
                ? `Excel erzeugen (${html.length} Datei${html.length === 1 ? "" : "en"})`
                : "Excel erzeugen";
        }
    }

    input.addEventListener("change", () => render(input.files));

    ["dragenter", "dragover"].forEach((ev) =>
        dropzone.addEventListener(ev, (e) => {
            e.preventDefault();
            dropzone.classList.add("is-dragover");
        })
    );
    ["dragleave", "drop"].forEach((ev) =>
        dropzone.addEventListener(ev, (e) => {
            e.preventDefault();
            dropzone.classList.remove("is-dragover");
        })
    );
    dropzone.addEventListener("drop", (e) => {
        if (e.dataTransfer && e.dataTransfer.files.length) {
            input.files = e.dataTransfer.files;
            render(input.files);
        }
    });
})();
