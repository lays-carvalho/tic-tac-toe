const socket = io();

// Toggle simples (para expandir/colapsar)
document.querySelectorAll(".toggle-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const content = btn.parentElement.nextElementSibling;
        if (!content) return;
        content.style.display = content.style.display === "none" ? "block" : "none";
        btn.textContent = btn.textContent === "+" ? "−" : "+";
    });
});

// Logout
document.getElementById("logoutBtn").addEventListener("click", async () => {
    await fetch("/logout", { method: "POST", credentials: "include" });
    window.location.href = "/login";
});

// Preencher lista de usuários criados
function populateList(elementId, items, formatter) {
    const el = document.getElementById(elementId);
    el.innerHTML = "";
    items.forEach(item => {
        const li = document.createElement("li");
        li.textContent = formatter(item);
        el.appendChild(li);
    });
}

// Inicializa monitor
async function initMonitor() {
    // Usuários criados
    const resAll = await fetch("/users/all", { credentials: "include" });
    const allUsers = await resAll.json();
    populateList("all-users-list", allUsers, u => `${u.username} (ID: ${u.id})`);

    // Usuários online
    const resOnline = await fetch("/users/online", { credentials: "include" });
    const onlineUsers = await resOnline.json();
    populateList("online-users-list", onlineUsers, u => `${u.username} (ID: ${u.id})`);
}

// Socket apenas para conexão inicial (opcional)
socket.on("connect", () => {
    console.log("Conectado ao monitor!");
    initMonitor();
});
