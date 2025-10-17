from bson import ObjectId

class GameRepository:
    def __init__(self, db):
        self.games = db["games"]

    def create_game(self, room_id, player_x, player_o):
        game = {
            "room_id": room_id,
            "player_x": {"id": player_x, "symbol": "X"},
            "player_o": {"id": player_o, "symbol": "O"},
            "state": [["" for _ in range(3)] for _ in range(3)],
            "turn": "X",
            "status": "In Progress",
            "winner": None
        }
        result = self.games.insert_one(game)
        game["_id"] = result.inserted_id
        return game

    def update_game(self, game_id, data):
        if not ObjectId.is_valid(game_id): return
        self.games.update_one({"_id": ObjectId(game_id)}, {"$set": data})

    def get_game(self, game_id):
        if not ObjectId.is_valid(game_id): return None
        return self.games.find_one({"_id": ObjectId(game_id)})