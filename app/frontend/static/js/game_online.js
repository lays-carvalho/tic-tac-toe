// game_online.js
export function startOnlineGame() {
  const socket = io();
  const params = new URLSearchParams(window.location.search);
  const roomId = params.get('room_id');

  const cells = Array.from(document.querySelectorAll(".cell"));
  const statusEl = document.getElementById("game-status");
  const playerMarkEl = document.getElementById("player-mark");
  const opponentNameEl = document.getElementById("opponent-name");
  const opponentMarkEl = document.getElementById("opponent-mark");
  const gameTitleEl = document.getElementById("game-title");
  const opponentIconEl = document.getElementById("opponent-icon");

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

  function updateGame(game) {
    renderBoard(game.state, game.winningCombo || []);
    if (game.status === 'Closed') {
      gameActive = false;
      if (game.winner === 'Empate') setStatus("O jogo empatou!");
      else setStatus(`O jogador ${game.winner} venceu!`);
    } else {
      gameActive = game.turn === myRole;
      setStatus(gameActive
        ? "Sua vez"
        : `Aguardando ${opponentNameEl.textContent}...`
      );
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
    }
  });

  cells.forEach(cell => cell.addEventListener("click", handleCellClick));
}
