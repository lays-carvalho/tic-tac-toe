export function initializeLobby() {
    let myData = null;
    let myRoom = null;
    let notifications = [];
    const socket = io();

    fetch('/users/me', { credentials: 'include' })
    .then(res => res.json())
    .then(user => {
        window.currentUser = user;
        socket.emit('register_user', { user_id: user._id });
    });

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
        bell: document.getElementById('notification-bell'),
        badge: document.getElementById('notification-badge'),
        notificationPanel: document.getElementById('notification-panel'),
        notificationList: document.getElementById('notification-list'),
        logoutBtn: document.getElementById('logoutBtn'),
        deleteAccountBtn: document.getElementById('deleteAccountBtn'),
        deleteModal: document.getElementById('confirmDeleteModal'),
        cancelDelete: document.getElementById('cancelDelete'),
        confirmDelete: document.getElementById('confirmDelete'),
    };

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
            : notifications.map((notif, i) => `
                <div class="notification-item">
                    <p><b>${notif.inviter_username}</b> te convidou para jogar!</p>
                    <div class="notification-actions">
                        <button class="notification-btn decline" data-index="${i}" data-room-id="${notif.room_id}">Recusar</button>
                        <button class="notification-btn accept" data-index="${i}" data-room-id="${notif.room_id}">Aceitar</button>
                    </div>
                </div>`).join('');
    };

    const updateUI = () => {
        if (!myRoom || !myData) return;

        if (myRoom.players.length > 1) {
            showOnlineView();
        }

        const me = myRoom.players.find(p => p.id === myData._id);
        const amIReady = myRoom.playersReady.find(p => p.id === myData._id)?.ready || false;

        if (me) ui.player1Panel.innerHTML = renderPlayerPanel(me, amIReady);

        const opponent = myRoom.players.find(p => p.id !== myData._id);
        if (opponent) {
            const oppReady = myRoom.playersReady.find(p => p.id === opponent.id)?.ready || false;
            ui.player2Panel.innerHTML = renderPlayerPanel(opponent, oppReady);
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
        }
    };

    const fetchOnlinePlayers = async () => {
        try {
            const response = await fetch("/users/online", { credentials: 'include' });
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
        } catch (e) {
            console.error("Erro ao buscar jogadores:", e);
        }
    };

    const fetchMyDataAndRoom = async () => {
        try {
            const meResponse = await fetch("/users/me", { credentials: 'include' });
            if (!meResponse.ok) {
                window.location.href = "/login";
                return;
            }
            myData = await meResponse.json();
            socket.emit('register_user', { user_id: myData._id });

            const roomResponse = await fetch("/rooms", { credentials: 'include' });
            myRoom = await roomResponse.json();
            updateUI();
        } catch (e) {
            console.error("Erro:", e);
        }
    };

    // --- SOCKET LISTENERS ---

    socket.on('online_users', (users) => {
        ui.playersList.innerHTML = users.length === 0
            ? '<li class="no-players">Nenhum jogador online.</li>'
            : users
                .filter(u => u.id !== currentUser._id) // ✅ ok
                .map(player => {
                    return `
                        <li>
                            <span class="status online"></span>
                            <span class="emoji">👤</span>
                            <span class="name">${player.username}</span>
                            <button class="btn-status invite-btn" data-player-id="${player.id}">
                                Convidar
                            </button>
                        </li>`;
                }).join('');
    });



    socket.on('new_invitation', ({ inviter_username, room_id }) => {
        notifications.push({ inviter_username, room_id });
        updateNotificationsUI();
        ui.bell?.classList.add('active');
    });

    socket.on('room_update', (room) => {
        myRoom = room;
        updateUI();
    });

    socket.on('connect', fetchMyDataAndRoom);

    

    // --- UI EVENT LISTENERS ---

    ui.playOnlineBtn.addEventListener('click', () => {
        showOnlineView();
        updateUI();
    });

    ui.bell?.addEventListener('click', () => {
        ui.notificationPanel.style.display = ui.notificationPanel.style.display === 'block' ? 'none' : 'block';
        ui.bell.classList.remove('active');
    });

    ui.notificationList?.addEventListener('click', async (e) => {
        const target = e.target;
        if (!target.classList.contains('notification-btn')) return;

        const roomId = target.dataset.roomId;
        notifications = notifications.filter(n => n.room_id !== roomId);
        updateNotificationsUI();

        if (target.classList.contains('accept')) {
            await fetch(`/rooms/join/${roomId}`, { method: 'POST', credentials: 'include' });
        } else {
            await fetch(`/rooms/${roomId}/decline`, { method: 'POST', credentials: 'include' });
        }
    });

    ui.playersList.addEventListener('click', async (e) => {
        const btn = e.target.closest('.invite-btn');
        if (btn && !btn.disabled) {
            btn.disabled = true;
            btn.textContent = 'Convidado';
            await fetch(`/rooms/${btn.dataset.playerId}/invite`, { method: 'POST', credentials: 'include' });
        }
    });

    ui.readyBtn.addEventListener('click', () => {
        if (myRoom) {
            fetch(`/rooms/${myRoom._id}/ready`, { method: 'POST', credentials: 'include' });
        }
    });

    ui.logoutBtn?.addEventListener('click', () => {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = "/logout";
        document.body.appendChild(form);
        form.submit();
    });

    if (ui.deleteAccountBtn) {
        ui.deleteAccountBtn.onclick = () => ui.deleteModal.style.display = 'flex';
        ui.cancelDelete.onclick = () => ui.deleteModal.style.display = 'none';
        ui.confirmDelete.onclick = () => {
            fetch("/users/me", { method: 'DELETE', credentials: 'include' })
                .then(res => res.ok ? window.location.href = "/" : alert('Erro ao apagar conta.'));
        };
    }
}
