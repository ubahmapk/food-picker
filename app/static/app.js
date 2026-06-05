let categories = [];
let places = [];
let currentVetoed = [];
let editingCategory = null;

const THEMES = ["auto", "light", "dark"];
const THEME_ICONS = { auto: "🌓", light: "☀️", dark: "🌙" };

function applyTheme(theme) {
    if (theme === "auto") {
        document.documentElement.removeAttribute("data-theme");
    } else {
        document.documentElement.setAttribute("data-theme", theme);
    }
    localStorage.setItem("theme", theme);
    const btn = document.getElementById("theme-toggle");
    if (btn) btn.textContent = THEME_ICONS[theme];
}

function cycleTheme() {
    const current = localStorage.getItem("theme") || "auto";
    const next = THEMES[(THEMES.indexOf(current) + 1) % THEMES.length];
    applyTheme(next);
}

function initTheme() {
    applyTheme(localStorage.getItem("theme") || "auto");
}

async function loadData() {
    try {
        const catsRes = await fetch("/api/categories");
        categories = await catsRes.json();

        const placesRes = await fetch("/api/places");
        places = await placesRes.json();

        renderCategoryToggles();
        renderPlacesList();
        renderCategoriesManageList();
    } catch (e) {
        console.error("Error loading data:", e);
    }
}

function renderCategoryToggles() {
    const container = document.getElementById("categories-list");
    container.innerHTML = "";

    categories.forEach((cat) => {
        const label = document.createElement("label");
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.id = `cat-${encodeURIComponent(cat)}`;
        cb.checked = true;
        label.appendChild(cb);
        label.appendChild(document.createTextNode(` ${cat}`));
        container.appendChild(label);
    });

    const placeList = document.getElementById("place-categories-list");
    placeList.innerHTML = "";
    categories.forEach((cat) => {
        const label = document.createElement("label");
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.className = "place-cat-checkbox";
        cb.value = cat;
        label.appendChild(cb);
        label.appendChild(document.createTextNode(` ${cat}`));
        placeList.appendChild(label);
    });
}

function getSelectedCategories() {
    const selected = [];
    categories.forEach((cat) => {
        const checkbox = document.getElementById(`cat-${encodeURIComponent(cat)}`);
        if (checkbox && checkbox.checked) {
            selected.push(cat);
        }
    });
    return selected;
}

async function makePick() {
    const selected = getSelectedCategories();
    const params = new URLSearchParams();

    selected.forEach((cat) => params.append("categories", cat));
    currentVetoed.forEach((name) => params.append("vetoed", name));

    try {
        const res = await fetch(`/api/pick?${params}`);

        if (res.status === 409) {
            document.getElementById("result").innerHTML =
                "<p><strong>No options remaining!</strong></p>";
            return;
        }

        const data = await res.json();

        document.getElementById("result").innerHTML = `
            <article style="padding: 1.5rem; text-align: center;">
                <h3>${escHtml(data.name)}</h3>
                <button id="veto-btn" style="margin-right: 0.5rem;">Veto - Pick Again</button>
                <button id="accept-btn" style="margin-left: 0.5rem;">That's It!</button>
            </article>
        `;
        document.getElementById("veto-btn").addEventListener("click", () => veto(data.name));
        document.getElementById("accept-btn").addEventListener("click", accept);
    } catch (e) {
        console.error("Error picking:", e);
    }
}

function renderVetoList() {
    const el = document.getElementById("veto-list");
    if (currentVetoed.length === 0) {
        el.innerHTML = "";
        return;
    }
    el.innerHTML =
        `<p><strong>Vetoed this session:</strong></p><ul>` +
        currentVetoed.map((n) => `<li>${escHtml(n)}</li>`).join("") +
        `</ul>`;
}

function veto(placeName) {
    currentVetoed.push(placeName);
    renderVetoList();
    makePick();
}

function accept() {
    currentVetoed = [];
    document.getElementById("result").innerHTML = "";
    renderVetoList();
}

async function addCategory() {
    const input = document.getElementById("new-category-input");
    const name = input.value.trim();

    if (!name) {
        alert("Category name is required");
        return;
    }

    try {
        const res = await fetch("/api/categories", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name }),
        });

        if (res.ok) {
            input.value = "";
            await loadData();
        } else {
            const err = await res.json();
            alert(`Error: ${err.error}`);
        }
    } catch (e) {
        console.error("Error adding category:", e);
    }
}

function escHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function renderPlacesList(editingName = null) {
    const container = document.getElementById("places-list");
    container.innerHTML = "";

    places.forEach((place) => {
        const item = document.createElement("article");
        item.style.padding = "1rem";
        if (place.name === editingName) {
            const catChecks = categories
                .map(
                    (c) =>
                        `<label style="display:flex;align-items:center;gap:0.4rem;margin:0.2rem 0;">` +
                        `<input type="checkbox" class="edit-cat-checkbox" value="${escHtml(c)}"${place.categories.includes(c) ? " checked" : ""}> ${escHtml(c)}` +
                        `</label>`,
                )
                .join("");
            item.innerHTML = `
                <input type="text" id="edit-name-input" value="${escHtml(place.name)}" style="margin-bottom:0.5rem;">
                <div style="margin-bottom:0.75rem;">${catChecks}</div>
                <button class="save-place-btn">Save</button>
                <button class="cancel-place-btn secondary outline" style="margin-left:0.5rem;">Cancel</button>
            `;
            item.querySelector(".save-place-btn").addEventListener("click", () => savePlace(place.name));
            item.querySelector(".cancel-place-btn").addEventListener("click", () => renderPlacesList());
        } else {
            item.innerHTML = `
                <strong>${escHtml(place.name)}</strong>
                <p style="margin: 0.5rem 0;">
                    ${place.categories.map((c) => `<span class="cat-tag">${escHtml(c)}</span>`).join("")}
                </p>
                <button class="edit-place-btn">Edit</button>
                <button class="delete-place-btn secondary outline" style="margin-left:0.5rem;">Delete</button>
            `;
            item.querySelector(".edit-place-btn").addEventListener("click", () => editPlace(place.name));
            item.querySelector(".delete-place-btn").addEventListener("click", () => deletePlace(place.name));
        }
        container.appendChild(item);
    });
}

function editPlace(name) {
    renderPlacesList(name);
}

async function savePlace(originalName) {
    const newName = document.getElementById("edit-name-input").value.trim();
    const selectedCats = [];
    document
        .querySelectorAll(".edit-cat-checkbox:checked")
        .forEach((cb) => selectedCats.push(cb.value));

    if (!newName || selectedCats.length === 0) {
        alert("Place name and at least one category are required");
        return;
    }

    const payload = { categories: selectedCats };
    if (newName !== originalName) payload.name = newName;

    try {
        const res = await fetch(`/api/places/${encodeURIComponent(originalName)}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (res.ok) {
            await loadData();
        } else {
            const err = await res.json();
            alert(`Error: ${err.error}`);
        }
    } catch (e) {
        console.error("Error saving place:", e);
    }
}

async function deletePlace(name) {
    if (!confirm(`Delete ${name}?`)) return;

    try {
        const res = await fetch(`/api/places/${encodeURIComponent(name)}`, {
            method: "DELETE",
        });

        if (res.ok) {
            await loadData();
        } else {
            const err = await res.json();
            alert(`Error: ${err.error}`);
        }
    } catch (e) {
        console.error("Error deleting place:", e);
    }
}

async function addPlace() {
    const input = document.getElementById("new-place-input");
    const name = input.value.trim();

    const selectedCats = [];
    document
        .querySelectorAll(".place-cat-checkbox:checked")
        .forEach((cb) => selectedCats.push(cb.value));

    if (!name || selectedCats.length === 0) {
        alert("Place name and at least one category are required");
        return;
    }

    try {
        const res = await fetch("/api/places", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, categories: selectedCats }),
        });

        if (res.ok) {
            input.value = "";
            document
                .querySelectorAll(".place-cat-checkbox")
                .forEach((cb) => (cb.checked = false));
            await loadData();
        } else {
            const err = await res.json();
            alert(`Error: ${err.error}`);
        }
    } catch (e) {
        console.error("Error adding place:", e);
    }
}

async function exportData(format) {
    try {
        window.location.href = `/api/export?format=${format}`;
    } catch (e) {
        console.error("Error exporting:", e);
    }
}

async function importData() {
    const fileInput = document.getElementById("import-file");
    const file = fileInput.files[0];

    if (!file) {
        alert("Select a file to import");
        return;
    }

    try {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch("/api/import", {
            method: "POST",
            body: formData,
        });

        if (res.ok) {
            fileInput.value = "";
            await loadData();
            alert("Import successful");
        } else {
            const err = await res.json();
            alert(`Error: ${err.error}`);
        }
    } catch (e) {
        console.error("Error importing:", e);
    }
}

function showHome() {
    document.getElementById("home").style.display = "block";
    document.getElementById("manage").style.display = "none";
    document.getElementById("about").style.display = "none";
}

function showManage() {
    document.getElementById("home").style.display = "none";
    document.getElementById("manage").style.display = "block";
    document.getElementById("about").style.display = "none";
    showManageTab("places");
}

async function showAbout() {
    document.getElementById("home").style.display = "none";
    document.getElementById("manage").style.display = "none";
    document.getElementById("about").style.display = "block";

    try {
        const res = await fetch("/api/about");
        const data = await res.json();
        const safeRepo = data.repo.startsWith("https://") ? escHtml(data.repo) : "#";
        document.getElementById("about-content").innerHTML = `
            <p>${escHtml(data.description)}</p>
            <dl>
                <dt>Tech stack</dt>
                <dd>${data.tech.map((t) => escHtml(t)).join(", ")}</dd>
                <dt>Source</dt>
                <dd><a href="${safeRepo}" target="_blank" rel="noopener">${escHtml(data.repo)}</a></dd>
            </dl>
        `;
    } catch (e) {
        console.error("Error loading about:", e);
    }
}

function showManageTab(tab) {
    document.querySelectorAll(".manage-panel").forEach((el) => (el.style.display = "none"));
    document.getElementById(`manage-${tab}`).style.display = "block";

    document.querySelectorAll(".tab-btn").forEach((btn) => btn.classList.add("outline"));
    document.getElementById(`tab-${tab}`).classList.remove("outline");
}

function renderCategoriesManageList() {
    const container = document.getElementById("categories-manage-list");
    if (!container) return;
    container.innerHTML = "";

    categories.forEach((cat) => {
        const item = document.createElement("article");
        item.style.padding = "1rem";
        if (cat === editingCategory) {
            item.innerHTML =
                `<input type="text" id="edit-category-input" value="${escHtml(cat)}" style="margin-bottom:0.5rem;">` +
                `<button class="save-cat-btn">Save</button>` +
                `<button class="cancel-cat-btn secondary outline" style="margin-left:0.5rem;">Cancel</button>`;
            item.querySelector(".save-cat-btn").addEventListener("click", () => saveCategory(cat));
            item.querySelector(".cancel-cat-btn").addEventListener("click", cancelEditCategory);
        } else {
            item.innerHTML =
                `<strong>${escHtml(cat)}</strong>` +
                `<button class="edit-cat-btn" style="margin-left:0.5rem;">Edit</button>` +
                `<button class="delete-cat-btn secondary outline" style="margin-left:0.5rem;">Delete</button>`;
            item.querySelector(".edit-cat-btn").addEventListener("click", () => editCategory(cat));
            item.querySelector(".delete-cat-btn").addEventListener("click", () => deleteCategory(cat));
        }
        container.appendChild(item);
    });
}

function editCategory(name) {
    editingCategory = name;
    renderCategoriesManageList();
}

function cancelEditCategory() {
    editingCategory = null;
    renderCategoriesManageList();
}

async function saveCategory(oldName) {
    const newName = document.getElementById("edit-category-input").value.trim();
    if (!newName) {
        alert("Category name is required");
        return;
    }

    try {
        const res = await fetch(`/api/categories/${encodeURIComponent(oldName)}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: newName }),
        });

        if (res.ok) {
            editingCategory = null;
            await loadData();
        } else {
            const err = await res.json();
            alert(`Error: ${err.error}`);
        }
    } catch (e) {
        console.error("Error renaming category:", e);
    }
}

async function deleteCategory(name) {
    if (!confirm(`Delete category "${name}"? Places with only this category will also be removed.`)) return;

    try {
        const res = await fetch(`/api/categories/${encodeURIComponent(name)}`, {
            method: "DELETE",
        });

        if (res.ok) {
            await loadData();
        } else {
            const err = await res.json();
            alert(`Error: ${err.error}`);
        }
    } catch (e) {
        console.error("Error deleting category:", e);
    }
}

initTheme();
loadData();
