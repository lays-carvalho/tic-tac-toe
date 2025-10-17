document.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname;
    
    // --- LÓGICA DE ROTEAMENTO DE SCRIPTS ---
    const params = new URLSearchParams(window.location.search);
    const mode = params.get("mode");

    if (path.startsWith('/game')) {
        if (mode === 'cpu') {
            import('./game_cpu.js').then(module => module.startCpuGame());
        } else if (mode === 'online') {
            import('./game_online.js').then(module => module.startOnlineGame());
        }
    } else if (path.startsWith('/lobby')) {
        // Carrega e inicializa a lógica do Lobby
        import('./lobby.js').then(module => module.initializeLobby());
    }
});