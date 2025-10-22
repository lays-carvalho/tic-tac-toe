// main.js
document.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname;
    const params = new URLSearchParams(window.location.search);
    const mode = params.get("mode");

    // Função para atualizar título e placar dinamicamente
    function updateGameUIForMode(mode) {
        const titleEl = document.getElementById("game-title");
        const opponentNameEl = document.getElementById("opponent-name");
        const opponentIconEl = document.getElementById("opponent-icon");

        if (!titleEl || !opponentNameEl || !opponentIconEl) return;

        if (mode === 'cpu') {
            titleEl.textContent = "Play vs CPU 🤖";
            opponentNameEl.textContent = "CPU";
            opponentIconEl.textContent = "🤖";
        } else if (mode === 'online') {
            titleEl.textContent = "Jogo Online ⚡";
            opponentNameEl.textContent = "Oponente";
            opponentIconEl.textContent = "👾";
        }
    }

    // Aplica as alterações visuais de acordo com o modo
    updateGameUIForMode(mode);

    // --- LÓGICA DE ROTEAMENTO DE SCRIPTS ---
    if (path.startsWith('/game')) {
        if (mode === 'cpu') {
            import('./game_cpu.js').then(module => module.startCpuGame());
        } else if (mode === 'online') {
            import('./game_online.js').then(module => module.startOnlineGame());
        }
    } else if (path.startsWith('/lobby')) {
        import('./lobby.js').then(module => module.initializeLobby());
    }
});
