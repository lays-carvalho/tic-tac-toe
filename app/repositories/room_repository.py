from bson import ObjectId
from datetime import datetime

class RoomRepository:
    def __init__(self, db):
        self.rooms = db["rooms"]

    def create_room(self, creator_id, username="Desconhecido"):
        room = {
            "creator": {"id": str(creator_id), "username": username},
            "players": [{"id": str(creator_id), "username": username}],
            "playersRoles": [],
            "playersReady": [{"id": str(creator_id), "username": username, "ready": False}],
            "playersInvited": [],
            "status": "Ativa", # Ativa, Completa, Em espera, In Progress, Finalizada
            "score": {"X": 0, "O": 0, "Empates": 0},
            "games": [],
            "last_activity": datetime.utcnow()
        }
        result = self.rooms.insert_one(room)
        room["_id"] = str(result.inserted_id)
        return room

    def get_room(self, room_id):
        if not ObjectId.is_valid(room_id): return None
        return self.rooms.find_one({"_id": ObjectId(room_id)})

    def update_room(self, room_id, data):
        if not ObjectId.is_valid(room_id): return
        data_to_update = data.copy()
        data_to_update.pop("_id", None)
        self.rooms.update_one({"_id": ObjectId(room_id)}, {"$set": data_to_update})

    def find_blocking_room(self, user_id):
        return self.rooms.find_one({
            "players.id": str(user_id),
            "status": {"$in": ["Ativa", "Em espera", "Completa", "In Progress"]}
        })

    def find_by_player(self, user_id):
        return list(self.rooms.find({"players.id": str(user_id)}))

    def find_room_by_creator(self, creator_id):
        return self.rooms.find_one({"creator.id": str(creator_id)})

    def get_all(self):
        return list(self.rooms.find({}))

    def delete_room(self, room_id):
        if not ObjectId.is_valid(room_id): return False
        result = self.rooms.delete_one({"_id": ObjectId(room_id)})
        return result.deleted_count > 0