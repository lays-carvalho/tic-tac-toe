from flask import request
from flask_socketio import emit, join_room, leave_room
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

    # ✅ Agora broadcast_online_users está dentro da função e pode usar user_service
    def broadcast_online_users():
        sessions = session_repo.get_all_sessions()
        online_list = []
        for s in sessions:
            user = user_service.get_by_id(s["user_id"])
            if user:
                online_list.append({"id": str(user["_id"]), "username": user["username"]})
        socketio.emit('online_users', online_list)

    @socketio.on('connect')
    def on_connect():
        print(f"Cliente conectado: {request.sid}")

    @socketio.on('register_user')
    def on_register_user(data):
        user_id = data.get('user_id')
        if user_id:
            user_sids[user_id] = request.sid
            print(f"Usuário {user_id} registrado com o SID {request.sid}")
            broadcast_online_users()


    @socketio.on('join_room')
    def on_join_room(data):
        room_id = data.get('room_id')
        user_id = data.get('user_id')

        if room_id and request.sid:
            join_room(room_id)
            print(f"✅ Usuário {user_id} entrou na sala {room_id} via socket.")
       

    @socketio.on('join_game_room')
    def on_join_game_room(data):
        room_id = data.get('room_id')
        if room_id:
            join_room(room_id)
            room = room_repo.get_room(room_id)
            if room and room.get('games'):
                game_id = room['games'][-1]
                game = game_service.game_repo.get_game(game_id)
                if game:
                    emit('game_state', {'room': convert_objectid(room), 'game': convert_objectid(game)})
            print(f"Cliente {request.sid} entrou na sala de jogo {room_id}")



    
    @socketio.on('make_move')
    def on_make_move(data):
        room_id = data.get('room_id')
        game_id = data.get('game_id')
        user_id = data.get('user_id')
        move = data.get('move')

        room, game, error = game_service.make_move(game_id, user_id, move)
        if error:
            emit('error', {'message': error})
        else:
            socketio.emit('game_update', {'room': convert_objectid(room), 'game': convert_objectid(game)}, to=room_id)

    @socketio.on('disconnect')
    def on_disconnect():
        disconnected_user_id = next((user_id for user_id, sid in user_sids.items() if sid == request.sid), None)
        
        if disconnected_user_id:
            user = user_service.get_by_id(disconnected_user_id)
            if user:
                print(f"Usuário {user.get('username')} desconectando...")
                
                # A função agora retorna o ID do oponente que ficou na sala
                opponent_id = room_service.leave_room(user["_id"], user["username"])

                # Se havia um oponente, vamos notificá-lo que o jogador saiu
                if opponent_id and opponent_id in user_sids:
                    # Pega o novo estado da sala do oponente (que agora deve estar sozinho)
                    new_opponent_room = room_service.get_user_room(opponent_id)
                    if new_opponent_room:
                        socketio.emit('room_update', convert_objectid(new_opponent_room), to=user_sids[opponent_id])

                # Remove a sessão do banco de dados
                session = session_repo.get_by_user(disconnected_user_id)
                if session:
                    session_repo.delete(session['token'])
                
                # Remove do mapeamento de SIDs
                if disconnected_user_id in user_sids:
                    del user_sids[disconnected_user_id]
                
                print(f"Usuário {user.get('username')} desconectado e sessão removida.")
                broadcast_online_users()