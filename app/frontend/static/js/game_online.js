// game_online.js
export function startOnlineGame() {
  const socket = io();
  const params = new URLSearchParams(window.location.search);
  const roomId = params.get('room_id');

  // Seletores da UI
  const cells = Array.from(document.querySelectorAll(".cell"));
  const statusEl = document.getElementById("game-status");
  const playerMarkEl = document.getElementById("player-mark");
  const opponentNameEl = document.getElementById("opponent-name");
  const opponentMarkEl = document.getElementById("opponent-mark");
  const gameTitleEl = document.getElementById("game-title");
  const opponentIconEl = document.getElementById("opponent-icon");
  const restartBtn = document.getElementById("restart");

  const playerWinsEl = document.getElementById("player-wins");
  const playerLossesEl = document.getElementById("player-losses");
  const playerDrawsEl = document.getElementById("player-draws");

  const oppWinsEl = document.getElementById("opponent-wins");
  const oppLossesEl = document.getElementById("opponent-losses");
  const oppDrawsEl = document.getElementById("opponent-draws");

  let myData = null;
  let myRole = null;
  let gameId = null;
  let gameActive = false;

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function renderBoard(boardState, winningCombo = []) {
    cells.forEach((cell, i) => {
      const row = Math.floor(i / 3);
      const col = i % 3;
      const mark = boardState[row][col];

      cell.textContent = mark;
      cell.classList.remove("win", "x-color", "o-color");
      if (mark === "X") cell.classList.add("x-color");
      if (mark === "O") cell.classList.add("o-color");
      if (winningCombo.includes(i)) cell.classList.add("win");
    });
  }

  function updateScoreboardOnline(result) {
    if (result === myRole) { // Vitória do jogador
      if (playerWinsEl) playerWinsEl.textContent = String(Number(playerWinsEl.textContent || 0) + 1);
      if (oppLossesEl) oppLossesEl.textContent = String(Number(oppLossesEl.textContent || 0) + 1);
    } else if (result === (myRole === 'X' ? 'O' : 'X')) { // Vitória do oponente
      if (oppWinsEl) oppWinsEl.textContent = String(Number(oppWinsEl.textContent || 0) + 1);
      if (playerLossesEl) playerLossesEl.textContent = String(Number(playerLossesEl.textContent || 0) + 1);
    } else if (result === 'Empate') { // Empate
      if (playerDrawsEl) playerDrawsEl.textContent = String(Number(playerDrawsEl.textContent || 0) + 1);
      if (oppDrawsEl) oppDrawsEl.textContent = String(Number(oppDrawsEl.textContent || 0) + 1);
    }
  }

  function handleCellClick(e) {
    if (!gameActive) return;

    const index = parseInt(e.currentTarget.dataset.index, 10);
    const row = Math.floor(index / 3);
    const col = index % 3;

    socket.emit('make_move', {
      room_id: roomId,
      game_id: gameId,
      user_id: myData._id,
      move: { row, col }
    });
  }

  window.leaveGame = function () {
    if (!myData) return;
    socket.emit('exit_game', { user_id: myData._id, room_id: roomId });
  };

  socket.on('return_to_lobby', () => {
    window.location.href = "/lobby";
  });

  function updateGame(game) {
    renderBoard(game.state, game.winningCombo || []);

    if (game.status === 'Closed') {
      gameActive = false;

      // Atualiza placar apenas uma vez
      if (!game.scoreUpdated) {
        if (game.winner === 'Empate') {
          setStatus("O jogo empatou!");
          updateScoreboardOnline('Empate');
        } else {
          setStatus(`O jogador ${game.winner} venceu!`);
          updateScoreboardOnline(game.winner);
        }
        game.scoreUpdated = true; // Marca que o placar já foi atualizado
      }

      if (restartBtn) restartBtn.style.display = "inline-block";

    } else {
      gameActive = game.turn === myRole;
      setStatus(gameActive
        ? "Sua vez"
        : `Aguardando ${opponentNameEl.textContent}...`
      );

      if (restartBtn) restartBtn.style.display = "none";
    }
  }

  socket.on('connect', () => {
    fetch('/users/me', { credentials: 'include' })
      .then(res => res.json())
      .then(userData => {
        myData = userData;
        socket.emit('register_user', { user_id: myData._id });
        socket.emit('join_game_room', { room_id: roomId, user_id: myData._id });
      });
  });

  socket.on('game_state', (data) => {
    const { game, my_role, opponent_username } = data;
    gameId = game._id;
    myRole = my_role;

    playerMarkEl.textContent = myRole;
    opponentNameEl.textContent = opponent_username;
    opponentMarkEl.textContent = myRole === 'X' ? 'O' : 'X';
    gameTitleEl.textContent = `Jogando contra ${opponent_username} ⚡`;
    opponentIconEl.textContent = "👾";

    updateGame(game);
  });

  socket.on('game_update', (data) => {
    const { game, my_role } = data;
    myRole = my_role;
    updateGame(game);
  });

  socket.on('room_update', (room) => {
    const opponent = room.players.find(p => p.id !== myData._id);
    if (!opponent) {
      setStatus("Oponente desconectou 😢");
      opponentNameEl.textContent = "Aguardando...";
      opponentMarkEl.textContent = myRole === 'X' ? 'O' : 'X';
      gameActive = false;

      if (restartBtn) restartBtn.style.display = "inline-block";
    }
  });

  socket.on('game_over', (data) => {
    setStatus(data.message);
    gameActive = false;

    if (data.score) {
        // Atualiza DOM com o score real do servidor
        if (playerWinsEl) playerWinsEl.textContent = data.score.me.wins;
        if (playerLossesEl) playerLossesEl.textContent = data.score.me.losses;
        if (playerDrawsEl) playerDrawsEl.textContent = data.score.me.draws;

        if (oppWinsEl) oppWinsEl.textContent = data.score.opponent.wins;
        if (oppLossesEl) oppLossesEl.textContent = data.score.opponent.losses;
        if (oppDrawsEl) oppDrawsEl.textContent = data.score.opponent.draws;
    }

    if (restartBtn) restartBtn.style.display = "inline-block";
  });


  socket.on('opponent_disconnected', (data) => {
    alert(data.message);
    window.location.href = "/lobby";
  });

  socket.on("restart_request", (data) => {
    if (!confirm(`${data.username} quer jogar novamente. Aceitar?`)) {
      socket.emit("restart_response", { room_id: roomId, accept: false, user_id: myData._id });
    } else {
      socket.emit("restart_response", { room_id: roomId, accept: true, user_id: myData._id });
    }
  });

  socket.on("restart_confirmed", () => {
    setStatus("Jogo reiniciado!");
    gameActive = true;
    if (restartBtn) restartBtn.style.display = "none";
  });

  socket.on("restart_denied", () => {
    alert("O adversário recusou reiniciar. Voltando ao lobby...");
    window.location.href = "/lobby";
  });

  if (restartBtn) {
    restartBtn.addEventListener("click", () => {
      socket.emit("request_restart", { room_id: roomId, user_id: myData._id });
      setStatus("Pedido de reinício enviado...");
    });
  }

  cells.forEach(cell => cell.addEventListener("click", handleCellClick));
}
