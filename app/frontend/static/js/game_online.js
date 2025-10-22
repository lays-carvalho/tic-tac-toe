// game_online.js
export function startOnlineGame() {
  const socket = io();
  const params = new URLSearchParams(window.location.search);
  const roomId = params.get('room_id');

  // Seletores da UI
  const cells = Array.from(document.querySelectorAll(".cell"));
  const statusEl = document.getElementById("game-status");
  const restartBtn = document.getElementById("restart");
  const playerMarkEl = document.getElementById("player-mark");
  const opponentNameEl = document.getElementById("opponent-name");
  const opponentMarkEl = document.getElementById("opponent-mark");
  const gameTitleEl = document.getElementById("game-title");
  const opponentIconEl = document.getElementById("opponent-icon");

  // Variáveis de estado
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
    if (!gameActive || !myRole) return;
    const index = parseInt(e.currentTarget.getAttribute("data-index"), 10);
    const row = Math.floor(index / 3);
    const col = index % 3;

    socket.emit('make_move', {
      room_id: roomId,
      game_id: gameId,
      user_id: myData._id,
      move: { row, col }
    });
  }
  
  // --- Eventos de Socket ---
  socket.on('connect', () => {
    console.log("Conectado ao servidor para o jogo.");
    socket.emit('join_game_room', { room_id: roomId });
  });

  socket.on('game_state', (data) => {
    const { room, game } = data;
    gameId = game._id;

    fetch('/users/me').then(res => res.json()).then(userData => {
      myData = userData;
      const myRoleData = room.playersRoles.find(p => p.id === myData._id);
      myRole = myRoleData.role;
      playerMarkEl.textContent = myRole;

      const opponentData = room.players.find(p => p.id !== myData._id);
      if (opponentData) {
        opponentNameEl.textContent = opponentData.username;
        opponentMarkEl.textContent = myRole === 'X' ? 'O' : 'X';
        gameTitleEl.textContent = `Jogando contra ${opponentData.username} ⚡`;
        opponentIconEl.textContent = "👾"; // você pode personalizar o emoji
      }

      updateGame(game);
    });
  });

  socket.on('game_update', (data) => {
    const { game } = data;
    updateGame(game);
  });
  
  socket.on('error', (data) => {
    setStatus(data.message);
    gameActive = false;
    setTimeout(() => { gameActive = true; }, 1500);
  });

  function updateGame(game) {
    renderBoard(game.state);
    
    if (game.status === 'Closed') {
      gameActive = false;
      if(game.winner === 'Empate') {
        setStatus("O jogo empatou!");
      } else {
        setStatus(`O jogador ${game.winner} venceu!`);
      }
    } else {
      gameActive = game.turn === myRole;
      setStatus(game.turn === myRole ? "Sua vez" : `Aguardando ${opponentNameEl.textContent}...`);
    }
  }

  // Adiciona listeners
  cells.forEach(cell => cell.addEventListener("click", handleCellClick));
}
