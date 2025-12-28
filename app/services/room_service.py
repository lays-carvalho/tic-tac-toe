import random
from datetime import datetime
from app.repositories.room_repository import RoomRepository
from app.repositories.game_repository import GameRepository

class RoomService:
    MAX_PLAYERS = 2

    def __init__(self, db):
        self.repo = RoomRepository(db)
        self.game_repo = GameRepository(db)

    def get_user_room(self, user_id):
        return self.repo.find_blocking_room(user_id)

    def create_or_get_room(self, user_id, username):
        room = self.get_user_room(user_id)
        if room:
            return room
        return self.repo.create_room(user_id, username)

    def send_invite(self, inviter_id, invitee_id, invitee_username):
        room = self.get_user_room(inviter_id)
        if not room: return None, "Você não tem uma sala ativa para convidar."
        if str(inviter_id) != str(room["creator"]["id"]): return None, "Apenas o dono da sala pode convidar jogadores."
        if len(room.get("players", [])) >= self.MAX_PLAYERS: return None, "Sua sala já está cheia."
        
        invitee_room = self.get_user_room(invitee_id)
        if invitee_room and len(invitee_room.get("players", [])) > 1: return None, "Jogador indisponível para jogar no momento."
        if any(p["id"] == invitee_id for p in room.get("playersInvited", [])): return None, "Convite já enviado para este jogador."

        room["playersInvited"].append({"id": invitee_id, "username": invitee_username})
        self.repo.update_room(str(room["_id"]), room)
        return room, None
    
    def accept_invite(self, user_id, username, room_id):
        room_to_join = self.repo.get_room(room_id)
        if not room_to_join: 
            return None, "Sala não encontrada. O anfitrião pode ter cancelado."

        if not any(p["id"] == user_id for p in room_to_join.get("playersInvited", [])):
            return None, "Você não foi convidado para esta sala."

        if len(room_to_join.get("players", [])) >= self.MAX_PLAYERS:
            return None, "A sala já está cheia."

        
        user_own_room = self.repo.find_room_by_creator(user_id)
        if user_own_room:
            self.repo.delete_room(str(user_own_room["_id"]))

        
        room_to_join["players"].append({"id": user_id, "username": username})
        room_to_join["playersReady"].append({"id": user_id, "username": username, "ready": False})
        room_to_join["playersInvited"] = [p for p in room_to_join["playersInvited"] if p["id"] != user_id]
        room_to_join["status"] = "Completa"

        
        if len(room_to_join["players"]) == 2:
            roles = random.sample(["X", "O"], 2)
            room_to_join["playersRoles"] = [
                {"id": room_to_join["players"][0]["id"], "username": room_to_join["players"][0]["username"], "role": roles[0]},
                {"id": room_to_join["players"][1]["id"], "username": room_to_join["players"][1]["username"], "role": roles[1]},
            ]

        self.repo.update_room(str(room_to_join["_id"]), room_to_join)
        return room_to_join, None


    

    def set_player_ready(self, room_id, user_id):
        room = self.repo.get_room(room_id)
        if not room: return None, "Sala não encontrada"
        player_ready = next((p for p in room["playersReady"] if p["id"] == user_id), None)
        if not player_ready: return None, "Você não faz parte desta sala"
        player_ready["ready"] = not player_ready["ready"]

        if len(room["players"]) == self.MAX_PLAYERS and all(p["ready"] for p in room["playersReady"]):
            room["status"] = "In Progress"
            player_x = next(p["id"] for p in room["playersRoles"] if p["role"] == "X")
            player_o = next(p["id"] for p in room["playersRoles"] if p["role"] == "O")
            game = self.game_repo.create_game(str(room["_id"]), player_x, player_o)
            room["games"].append(str(game["_id"]))
        
        self.repo.update_room(str(room["_id"]), room)
        return room, None

    def leave_room(self, user_id, username):
        room = self.get_user_room(user_id)
        opponent_id = None
        if not room:
            self.create_or_get_room(user_id, username)
            return None 

        if str(room["creator"]["id"]) == user_id:
            self.repo.delete_room(str(room["_id"]))
            opponent = next((p for p in room["players"] if p["id"] != user_id), None)
            if opponent:
                opponent_id = opponent["id"]
                self.create_or_get_room(opponent["id"], opponent["username"])
        else:
            opponent_id = room["creator"]["id"] 
            room["players"] = [p for p in room.get("players", []) if p["id"] != user_id]
            room["playersReady"] = [p for p in room.get("playersReady", []) if p["id"] != user_id]
            room["playersRoles"] = []
            room["status"] = "Ativa"
            self.repo.update_room(str(room["_id"]), room)
        
        self.create_or_get_room(user_id, username)
        return opponent_id 

    def decline_invite(self, room_id, user_id):
        room = self.repo.get_room(room_id)
        if not room: return None, "Sala não encontrada"
        room["playersInvited"] = [p for p in room.get("playersInvited", []) if p["id"] != user_id]
        self.repo.update_room(str(room["_id"]), room)
        return room, None
    
    def mark_empty_rooms_inactive(self):
        all_rooms = self.repo.get_all()
        for room in all_rooms:
            if not room.get("players") and room["status"] != "Finalizada":
                room["status"] = "Inativa"
                self.repo.update_room(str(room["_id"]), room)