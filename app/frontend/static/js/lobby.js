export function initializeLobby() {
    let myData = null;
    let myRoom = null;
    let notifications = [];
    const socket = io();

    // Mapeamento dos elementos da interface
    const ui = {
        playOnlineBtn: document.getElementById('play-online-btn'),
        onlineSection: document.getElementById('online-section'),
        vsPanelSection: document.getElementById('vs-panel-section'),
        startGameSection: document.getElementById('start-game-section'),
        buttonsContainer: document.querySelector('.buttons'),
        subtitle: document.getElementById('subtitle'),
        playersList: document.getElementById('players-list'),
        player1Panel: document.getElementById('player1-panel'),
        player2Panel: document.getElementById('player2-panel'),
        readyBtn: document.getElementById('readyBtn'),
        gameStatus: document.getElementById('game-status'),
        bell: document.getElementById('notification-bell'),
        badge: document.getElementById('notification-badge'),
        notificationPanel: document.getElementById('notification-panel'),
        notificationList: document.getElementById('notification-list'),
        deleteModal: document.getElementById('confirmDeleteModal'),
        logoutBtn: document.getElementById('logoutBtn'),
        deleteAccountBtn: document.getElementById('deleteAccountBtn'),
        cancelDelete: document.getElementById('cancelDelete'),
        confirmDelete: document.getElementById('confirmDelete'),
    };

    // Funções de UI
    const showOnlineView = () => {
        ui.buttonsContainer.style.display = 'none';
        ui.subtitle.textContent = 'Convide um jogador para começar';
        ui.onlineSection.style.display = 'block';
        ui.vsPanelSection.style.display = 'flex';
        ui.startGameSection.style.display = 'flex';
    };

    const renderPlayerPanel = (player, ready) => {
        const isYou = player.id === myData._id ? ' (Você)' : '';
        return `
            <div class="player-info">
                <span class="emoji">👾</span>
                <p class="player-name">${player.username}${isYou}</p>
            </div>
            <div class="lights">
                <span class="light red">🔴</span>
                <span class="light yellow">🟡</span>
                <span class="light green ${ready ? '' : 'disabled'}">🟢</span>
            </div>`;
    };

    const renderWaitingPanel = () => `
        <div class="player-info">
            <span class="emoji loader"></span>
            <p class="player-name">Aguardando oponente...</p>
        </div>
        <div class="lights">
            <span class="light red">🔴</span>
            <span class="light yellow">🟡</span>
            <span class="light green disabled">🟢</span>
        </div>`;
    
    const updateNotificationsUI = () => {
        if (!ui.badge || !ui.notificationList) return;
        ui.badge.style.display = notifications.length > 0 ? 'block' : 'none';
        ui.badge.textContent = notifications.length;

        ui.notificationList.innerHTML = notifications.length === 0
            ? '<p class="no-invites">Nenhum convite</p>'
            : notifications.map((notif, index) => `
                <div class="notification-item">
                    <p><b>${notif.inviter_username}</b> te convidou para jogar!</p>
                    <div class="notification-actions">
                        <button class="notification-btn decline" data-index="${index}" data-room-id="${notif.room_id}">Recusar</button>
                        <button class="notification-btn accept" data-index="${index}" data-room-id="${notif.room_id}">Aceitar</button>
                    </div>
                </div>`).join('');
    };

    const updateUI = () => {
        if (!myRoom || !myData) return;

        if (myRoom.players.length > 1) {
            showOnlineView();
        }

        const meInRoom = myRoom.players.find(p => p.id === myData._id);
        const amIReady = myRoom.playersReady.find(p => p.id === myData._id)?.ready || false;

        if (meInRoom) ui.player1Panel.innerHTML = renderPlayerPanel(meInRoom, amIReady);

        const opponent = myRoom.players.find(p => p.id !== myData._id);
        if (opponent) {
            const isOpponentReady = myRoom.playersReady.find(p => p.id === opponent.id)?.ready || false;
            ui.player2Panel.innerHTML = renderPlayerPanel(opponent, isOpponentReady);
            ui.player2Panel.classList.remove('waiting');
        } else {
            ui.player2Panel.innerHTML = renderWaitingPanel();
            ui.player2Panel.classList.add('waiting');
        }

        ui.readyBtn.style.display = myRoom.players.length === 2 ? 'block' : 'none';
        if (ui.readyBtn.style.display === 'block') {
            ui.readyBtn.textContent = amIReady ? 'Pronto!' : 'Estou Pronto';
            ui.readyBtn.classList.toggle('ready', amIReady);
        }

        if (myRoom.status === "In Progress") {
            window.location.href = `/game?mode=online&room_id=${myRoom._id}`;
        } else if (myRoom.players.length < 2) {
            ui.gameStatus.textContent = "Aguarde um oponente...";
        } else {
            const readyCount = myRoom.playersReady.filter(p => p.ready).length;
            ui.gameStatus.textContent = `${readyCount}/2 jogadores prontos`;
        }
    };
    
    const fetchOnlinePlayers = async () => {
        try {
            const response = await fetch("/users/online");
            const players = await response.json();
            
            ui.playersList.innerHTML = players.length === 0
                ? '<li class="no-players">Nenhum jogador online.</li>'
                : players.map(player => {
                    const isInvited = myRoom?.playersInvited.some(p => p.id === player.id);
                    return `
                        <li>
                            <span class="status online"></span>
                            <span class="emoji">👤</span>
                            <span class="name">${player.username}</span>
                            <button class="btn-status invite-btn" data-player-id="${player.id}" ${isInvited ? 'disabled' : ''}>
                                ${isInvited ? 'Convidado' : 'Convidar'}
                            </button>
                        </li>`;
                }).join('');
        } catch (e) { console.error("Erro ao buscar jogadores:", e); }
    };

    const fetchMyDataAndRoom = async () => {
        try {
            const meResponse = await fetch("/users/me");
            if (!meResponse.ok) {
                window.location.href = "/login";
                return;
            }
            myData = await meResponse.json();
            socket.emit('register_user', { user_id: myData._id });
            
            const roomResponse = await fetch("/rooms");
            myRoom = await roomResponse.json();
            updateUI();
            await fetchOnlinePlayers();
        } catch(e) { console.error("Erro ao buscar dados:", e); }
    };

    // --- Listeners de Socket ---
    socket.on('connect', () => {
        console.log("Conectado ao servidor de sockets.");
        fetchMyDataAndRoom();
    });

    socket.on('new_invitation', (data) => {
        if (!notifications.some(n => n.room_id === data.room_id)) {
            notifications.push(data);
            if(ui.bell) ui.bell.classList.add('active');
            updateNotificationsUI();
        }
    });

    socket.on('room_update', (data) => {
        myRoom = data;
        updateUI();
        fetchOnlinePlayers();
    });

    // --- Listeners de Eventos da UI ---
    ui.playOnlineBtn.addEventListener('click', () => {
        showOnlineView();
        updateUI();
        fetchOnlinePlayers();
    });
    
    if(ui.bell) {
        ui.bell.addEventListener('click', () => {
            ui.notificationPanel.style.display = ui.notificationPanel.style.display === 'block' ? 'none' : 'block';
            ui.bell.classList.remove('active');
        });
    }

    if(ui.notificationList) {
        ui.notificationList.addEventListener('click', async (e) => {
            const target = e.target;
            if (!target.classList.contains('notification-btn')) return;

            const roomId = target.dataset.roomId;
            notifications = notifications.filter(n => n.room_id !== roomId);
            updateNotificationsUI();

            if (target.classList.contains('accept')) {
                await fetch(`/rooms/join/${roomId}`, { method: 'POST' });
            } else if (target.classList.contains('decline')) {
                await fetch(`/rooms/${roomId}/decline`, { method: 'POST' });
            }
        });
    }
    
    ui.playersList.addEventListener('click', async (e) => {
        const btn = e.target.closest('.invite-btn');
        if (btn && !btn.disabled) {
            btn.disabled = true;
            btn.textContent = 'Convidado';
            const inviteeId = btn.dataset.playerId;
            await fetch(`/rooms/${inviteeId}/invite`, { method: 'POST' });
        }
    });

    ui.readyBtn.addEventListener('click', () => {
        if (myRoom) {
            fetch(`/rooms/${myRoom._id}/ready`, { method: 'POST' });
        }
    });
    
    if(ui.logoutBtn) {
        ui.logoutBtn.addEventListener('click', () => {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = "/logout";
            document.body.appendChild(form);
            form.submit();
        });
    }
    
    if(ui.deleteAccountBtn) {
        ui.deleteAccountBtn.onclick = () => ui.deleteModal.style.display = 'flex';
        ui.cancelDelete.onclick = () => ui.deleteModal.style.display = 'none';
        ui.confirmDelete.onclick = () => {
            fetch("/users/me", { method: 'DELETE' })
                .then(res => {
                    if (res.ok) window.location.href = "/";
                    else alert('Erro ao apagar conta.');
                });
        };
    }
}