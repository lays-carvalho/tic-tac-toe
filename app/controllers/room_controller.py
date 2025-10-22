from flask import Blueprint, jsonify, request
from app.services.room_service import RoomService
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.utils.auth_decorator import token_required
from app.utils.mongo_utils import convert_objectid
from app import db, socketio
from app.sockets.game_socket import user_sids

room_bp = Blueprint("rooms", __name__)
room_service = RoomService(db)
user_service = UserService(UserRepository(db))

@room_bp.route("/rooms", methods=["GET"])
@token_required()
def get_my_room(current_user):
    room = room_service.get_user_room(str(current_user["_id"]))
    if not room:
        room = room_service.create_or_get_room(str(current_user["_id"]), current_user["username"])
    return jsonify(convert_objectid(room))

@room_bp.route("/rooms/<invitee_id>/invite", methods=["POST"])
@token_required()
def invite_player(current_user, invitee_id):
    invitee = user_service.get_by_id(invitee_id)
    if not invitee:
        return jsonify({"error": "Usuário convidado não encontrado"}), 404

    room, error = room_service.send_invite(str(current_user["_id"]), invitee_id, invitee["username"])
    if error:
        return jsonify({"error": error}), 400

    room_json = convert_objectid(room)  # ✅ garante serialização

    # Notifica jogador convidado
    if invitee_id in user_sids:
        invitee_sid = user_sids[invitee_id]
        invitation_data = {
            "inviter_username": current_user["username"],
            "room_id": str(room["_id"])
        }
        socketio.emit('new_invitation', invitation_data, to=invitee_sid)

    # Atualiza a sala no painel do anfitrião
    host_sid = user_sids.get(str(current_user["_id"]))
    if host_sid:
        socketio.emit('room_update', room_json, to=host_sid)

    return jsonify(room_json)

@room_bp.route("/rooms/join/<room_id>", methods=["POST"])
@token_required()
def join_room(current_user, room_id):
    room, error = room_service.accept_invite(str(current_user["_id"]), current_user["username"], room_id)
    if error:
        return jsonify({"error": error}), 400

    room = convert_objectid(room)  # garante que ObjectId e datetime são strings

    # 1️⃣ Enviar atualização para todos os jogadores conectados da sala
    for player in room["players"]:
        sid = user_sids.get(player["id"])
        if sid:
            socketio.emit('room_update', room, to=sid)

    # 2️⃣ Retornar para quem aceitou (útil para o front atualizar também)
    return jsonify(room)




@room_bp.route("/rooms/<room_id>/decline", methods=["POST"])
@token_required()
def decline_invite(current_user, room_id):
    room, error = room_service.decline_invite(room_id, str(current_user["_id"]))
    if error: return jsonify({"error": error}), 400
    return jsonify({"message": "Convite recusado com sucesso."})

@room_bp.route("/rooms/<room_id>/ready", methods=["POST"])
@token_required()
def start_game(current_user, room_id):
    room, error = room_service.set_player_ready(room_id, str(current_user["_id"]))
    if error: return jsonify({"error": error}), 400

    # Notifica ambos os jogadores sobre a mudança de status (pronto/não pronto)
    for player in room['players']:
        if player['id'] in user_sids:
            socketio.emit('room_update', convert_objectid(room), to=user_sids[player['id']])
            
    return jsonify(convert_objectid(room))