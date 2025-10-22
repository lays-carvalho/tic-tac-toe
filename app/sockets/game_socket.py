# game_socket.py
from flask import request
from flask_socketio import emit, join_room
from app.services.game_service import GameService
from app.services.room_service import RoomService
from app.services.user_service import UserService
from app.repositories.room_repository import RoomRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.utils.mongo_utils import convert_objectid
from app import db, socketio

user_sids = {}
session_repo = SessionRepository(db)

def register_game_events(socketio, db):
    game_service = GameService(db)
    room_service = RoomService(db)
    user_service = UserService(UserRepository(db))
    room_repo = RoomRepository(db)

    # Guarda pedidos de restart: {room_id: [user_id1, user_id2]}
    restart_requests = {}

    def broadcast_online_users():
        sessions = session_repo.get_all_sessions()
        online_list = [
            {"id": str(user["_id"]), "username": user["username"]}
            for s in sessions if (user := user_service.get_by_id(s["user_id"]))
        ]
        socketio.emit('online_users', online_list)

    @socketio.on('connect')
    def on_connect():
        print(f"Cliente conectado: {request.sid}")

    @socketio.on('register_user')
    def on_register_user(data):
        user_id = data.get('user_id')
        if user_id:
            user_sids[user_id] = request.sid
            broadcast_online_users()

    @socketio.on('join_game_room')
    def on_join_game_room(data):
        room_id = data.get('room_id')
        user_id = data.get('user_id')
        if not room_id or not user_id: return

        join_room(room_id)
        room = room_repo.get_room(room_id)
        if not room or not room.get('games'): return
        game_id = room['games'][-1]
        game = game_service.game_repo.get_game(game_id)
        if not game: return

        for player in room['players']:
            sid = user_sids.get(str(player['id']))
            if not sid: continue
            role_entry = next((r for r in room.get("playersRoles", []) if r["id"] == player["id"]), None)
            my_role = role_entry["role"] if role_entry else "X"
            opponent = next((p for p in room['players'] if p['id'] != player['id']), None)

            emit(
                'game_state',
                {
                    'room': convert_objectid(room),
                    'game': convert_objectid(game),
                    'my_role': my_role,
                    'my_username': player["username"],
                    'opponent_username': opponent["username"] if opponent else "Aguardando..."
                },
                to=sid
            )

    @socketio.on('make_move')
    def on_make_move(data):
        room_id = data.get('room_id')
        game_id = data.get('game_id')
        user_id = data.get('user_id')
        move = data.get('move')

        room, game, error = game_service.make_move(game_id, user_id, move)
        if error:
            emit('error', {'message': error})
            return

        for player in room['players']:
            sid = user_sids.get(str(player['id']))
            if not sid: continue
            role_entry = next((r for r in room.get("playersRoles", []) if r["id"] == player['id']), None)
            my_role = role_entry["role"] if role_entry else "X"
            opponent = next((p for p in room['players'] if p['id'] != player['id']), None)

            socketio.emit(
                'game_update',
                {
                    'room': convert_objectid(room),
                    'game': convert_objectid(game),
                    'my_role': my_role,
                    'my_username': player["username"],
                    'opponent_username': opponent["username"] if opponent else "Aguardando..."
                },
                to=sid
            )

    # --- NOVO: Solicitar restart ---
    @socketio.on('request_restart')
    def on_request_restart(data):
        room_id = data.get('room_id')
        user_id = data.get('user_id')
        if not room_id or not user_id: return

        room = room_repo.get_room(room_id)
        if not room or not room.get('players'): return

        opponent = next((p for p in room['players'] if str(p['id']) != str(user_id)), None)
        if not opponent: return

        restart_requests[room_id] = restart_requests.get(room_id, [])
        restart_requests[room_id].append(user_id)

        sid = user_sids.get(str(opponent['id']))
        if sid:
            socketio.emit("restart_request", {"username": user_service.get_by_id(user_id)['username']}, to=sid)

    @socketio.on('restart_response')
    def on_restart_response(data):
        room_id = data.get('room_id')
        accept = data.get('accept')
        user_id = data.get('user_id')
        if not room_id or not user_id: return

        room = room_repo.get_room(room_id)
        if not room or not room.get('players'): return

        players = [p for p in room['players']]
        if len(players) != 2: return

        if accept:
            # Cria novo game
            game_id = game_service.create_game(room_id)
            room['games'].append(game_id)
            room_repo.update_room(str(room['_id']), room)

            # Envia novo estado para cada jogador
            for player in players:
                sid = user_sids.get(str(player['id']))
                if not sid:
                    continue
                role_entry = next((r for r in room.get("playersRoles", []) if r["id"] == player["id"]), None)
                my_role = role_entry["role"] if role_entry else "X"
                opponent = next((p for p in room['players'] if p['id'] != player['id']), None)
                new_game = game_service.game_repo.get_game(game_id)

                socketio.emit(
                    'game_state',
                    {
                        'room': convert_objectid(room),
                        'game': convert_objectid(new_game),
                        'my_role': my_role,
                        'my_username': player["username"],
                        'opponent_username': opponent["username"] if opponent else "Aguardando..."
                    },
                    to=sid
                )
        else:
            requester_id = next((rid for rid in restart_requests.get(room_id, []) if rid != user_id), None)
            if requester_id and requester_id in user_sids:
                socketio.emit("restart_denied", {}, to=user_sids[requester_id])

        restart_requests.pop(room_id, None)


    @socketio.on('game_over')
    def on_game_over(data):
        room_id = data.get('room_id')
        winner = data.get('winner')

        room = room_repo.get_room(room_id)
        if not room: return

        # Atualiza placar interno do room
        for player in room.get('players', []):
            role_entry = next((r for r in room.get("playersRoles", []) if r["id"] == player['id']), None)
            player_role = role_entry["role"] if role_entry else None

            if 'score' not in player:
                player['score'] = {'wins': 0, 'losses': 0, 'draws': 0}

            if winner == 'Empate':
                player['score']['draws'] += 1
            elif winner in ['X', 'O']:
                if player_role == winner:
                    player['score']['wins'] += 1
                else:
                    player['score']['losses'] += 1

        # Atualiza a sala no DB
        room_repo.update_room(str(room['_id']), room)

        # Envia game_over + score para cada jogador
        for player in room.get('players', []):
            sid = user_sids.get(str(player['id']))
            if not sid: continue

            role_entry = next((r for r in room.get("playersRoles", []) if r["id"] == player['id']), None)
            player_role = role_entry["role"] if role_entry else None
            opponent = next((p for p in room['players'] if str(p['id']) != str(player['id'])), None)

            if winner in ['X', 'O']:
                msg = "Você venceu!" if player_role == winner else "Você perdeu!"
            else:
                msg = "Empate!"

            socketio.emit('game_over', {
                'winner': winner,
                'message': msg,
                'score': {
                    'me': player['score'],
                    'opponent': opponent['score'] if opponent else {'wins':0,'losses':0,'draws':0}
                }
            }, to=sid)


    @socketio.on('disconnect')
    def on_disconnect():
        disconnected_user_id = next((uid for uid, sid in user_sids.items() if sid == request.sid), None)
        if not disconnected_user_id: return
        user_sids.pop(disconnected_user_id, None)
        broadcast_online_users()

    @socketio.on('exit_game')
    def on_exit_game(data):
        user_id = data.get('user_id')
        room_id = data.get('room_id')
        if not user_id or not room_id: return

        print(f"Usuário {user_id} saiu manualmente do jogo.")
        try:
            opponent_id = room_service.leave_room(user_id, None)
            if opponent_id and opponent_id in user_sids:
                socketio.emit("opponent_disconnected", {"message": "O jogador saiu do jogo."}, to=user_sids[opponent_id])
        except Exception as e:
            print("Erro ao remover jogador da sala:", e)

        sid = user_sids.get(user_id)
        if sid:
            socketio.emit("return_to_lobby", {}, to=sid)

        print("Jogador saiu do jogo e voltou ao lobby com segurança.")
