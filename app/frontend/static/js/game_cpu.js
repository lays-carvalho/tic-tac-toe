export function startCpuGame() {
  // seletores
  const cells = Array.from(document.querySelectorAll(".cell"));
  const statusEl = document.getElementById("game-status");
  const restartBtn = document.getElementById("restart");

  const playerWinsEl = document.getElementById("player-wins");
  const playerLossesEl = document.getElementById("player-losses");
  const playerDrawsEl = document.getElementById("player-draws");

  const oppWinsEl = document.getElementById("opponent-wins");
  const oppLossesEl = document.getElementById("opponent-losses");
  const oppDrawsEl = document.getElementById("opponent-draws");

  // estado do jogo
  let board = ["", "", "", "", "", "", "", "", ""];
  let gameActive = true;

  // combinações vencedoras
  const wins = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8], // linhas
    [0, 3, 6], [1, 4, 7], [2, 5, 8], // colunas
    [0, 4, 8], [2, 4, 6]             // diagonais
  ];

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function renderBoard() {
    cells.forEach((cell, i) => {
      cell.textContent = board[i];
      cell.classList.remove("win", "x-color", "o-color");
      if (board[i] === "X") cell.classList.add("x-color");
      if (board[i] === "O") cell.classList.add("o-color");
    });
  }

  function checkWinner(bd) {
    for (let combo of wins) {
      const [a, b, c] = combo;
      if (bd[a] && bd[a] === bd[b] && bd[a] === bd[c]) {
        return { winner: bd[a], combo };
      }
    }
    if (!bd.includes("")) return { winner: "draw" };
    return null;
  }

  function updateScoreboard(result) {
    if (result === "X") {
      if (playerWinsEl) playerWinsEl.textContent = String(Number(playerWinsEl.textContent || 0) + 1);
      if (oppLossesEl) oppLossesEl.textContent = String(Number(oppLossesEl.textContent || 0) + 1);
    } else if (result === "O") {
      if (oppWinsEl) oppWinsEl.textContent = String(Number(oppWinsEl.textContent || 0) + 1);
      if (playerLossesEl) playerLossesEl.textContent = String(Number(playerLossesEl.textContent || 0) + 1);
    } else if (result === "draw") {
      if (playerDrawsEl) playerDrawsEl.textContent = String(Number(playerDrawsEl.textContent || 0) + 1);
      if (oppDrawsEl) oppDrawsEl.textContent = String(Number(oppDrawsEl.textContent || 0) + 1);
    }
  }

  function endGame(result) {
    gameActive = false;
    if (result === "draw") {
        setStatus("Empate!");
    } else {
      const winInfo = checkWinner(board);
      setStatus(`Jogador ${winInfo.winner} venceu!`);
      if (winInfo && winInfo.combo) {
          winInfo.combo.forEach((i) => cells[i].classList.add("win"));
      }
    }
    updateScoreboard(result);
    if (restartBtn) restartBtn.style.display = "inline-block";
  }

  function cpuChooseMove() {
    const me = "O";
    const you = "X";

    function findWinningMove(mark) {
      for (let combo of wins) {
        const [a, b, c] = combo;
        const vals = [board[a], board[b], board[c]];
        const indices = [a, b, c];
        const countMark = vals.filter((v) => v === mark).length;
        const countEmpty = vals.filter((v) => v === "").length;
        if (countMark === 2 && countEmpty === 1) {
          return indices[vals.indexOf("")];
        }
      }
      return null;
    }
    
    let idx = findWinningMove(me) || findWinningMove(you);
    if (idx !== null) return idx;

    const empties = board.map((v, i) => (v === "" ? i : null)).filter((i) => i !== null);
    return empties[Math.floor(Math.random() * empties.length)];
  }

  function handleCellClick(e) {
    if (!gameActive) return;
    const idx = Number(e.currentTarget.getAttribute("data-index"));
    if (board[idx] !== "") return;
    board[idx] = "X";
    renderBoard();

    const outcome = checkWinner(board);
    if (outcome) {
      endGame(outcome.winner);
      return;
    }

    setStatus("CPU está pensando... ⏳");
    gameActive = false;
    setTimeout(() => {
      const move = cpuChooseMove();
      if (move !== null) board[move] = "O";
      renderBoard();

      const out2 = checkWinner(board);
      if (out2) {
        endGame(out2.winner);
      } else {
        gameActive = true;
        setStatus("Sua vez (X)");
      }
    }, 1000);
  }

  function restartGame() {
    board = ["", "", "", "", "", "", "", "", ""];
    gameActive = true;
    renderBoard();
    setStatus("Sua vez (X)");
    if (restartBtn) restartBtn.style.display = "none";
  }

  function attachListeners() {
    cells.forEach((cell) => {
      cell.addEventListener("click", handleCellClick);
    });

    if (restartBtn) {
      restartBtn.addEventListener("click", restartGame);
    }
  }

  restartGame();
  attachListeners();
}