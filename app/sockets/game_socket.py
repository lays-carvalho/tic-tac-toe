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
            role_entry = next((r for r in room.get("playersRoles", []) if r["id"] == player["id"]), None)
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

    @socketio.on('disconnect')
    def on_disconnect():
        disconnected_user_id = next((uid for uid, sid in user_sids.items() if sid == request.sid), None)
        if not disconnected_user_id: return
        user_sids.pop(disconnected_user_id, None)
        broadcast_online_users()
