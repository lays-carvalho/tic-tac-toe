class MatchRepository:
    def __init__(self, db):
        self.matches = db["matches"]

    def create_match(self, player_x, player_o):
        match = {
            "player_x": player_x,
            "player_o": player_o,
            "state": [["" for _ in range(3)] for _ in range(3)],
            "turn": "X",
            "winner": None
        }
        self.matches.insert_one(match)
        return match

    def update_match(self, match_id, state, turn, winner):
        self.matches.update_one(
            {"_id": match_id},
            {"$set": {"state": state, "turn": turn, "winner": winner}}
        )
