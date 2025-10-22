# game_service.py
from app.repositories.game_repository import GameRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.user_repository import UserRepository

class GameService:
    def __init__(self, db):
        self.game_repo = GameRepository(db)
        self.room_repo = RoomRepository(db)
        self.user_repo = UserRepository(db)

    def make_move(self, game_id, user_id, move):
        game = self.game_repo.get_game(game_id)
        if not game: return None, None, "Partida não encontrada"

        room = self.room_repo.get_room(game["room_id"])
        if not room: return None, None, "Sala não encontrada"

        if game["status"] != "In Progress":
            return room, game, "A partida já terminou"

        player_symbol = "X" if game["player_x"]["id"] == user_id else "O" if game["player_o"]["id"] == user_id else None
        if not player_symbol: return room, game, "Você não participa desta partida"
        if player_symbol != game["turn"]: return room, game, "Não é sua vez"

        row, col = move['row'], move['col']
        if game["state"][row][col] != "": return room, game, "Esta célula já está ocupada"

        game["state"][row][col] = player_symbol
        winner = self._check_winner(game["state"])

        if winner:
            game["winner"] = winner
            game["status"] = "Closed"
            if winner == "X":
                self.user_repo.update_stats(game["player_x"]["id"], "wins")
                self.user_repo.update_stats(game["player_o"]["id"], "losses")
            elif winner == "O":
                self.user_repo.update_stats(game["player_o"]["id"], "wins")
                self.user_repo.update_stats(game["player_x"]["id"], "losses")
            else:
                self.user_repo.update_stats(game["player_x"]["id"], "draws")
                self.user_repo.update_stats(game["player_o"]["id"], "draws")

            if winner == "Empate": room["score"]["Empates"] += 1
            else: room["score"][winner] += 1
            self.room_repo.update_room(room["_id"], room)
        else:
            game["turn"] = "O" if game["turn"] == "X" else "X"

        self.game_repo.update_game(game_id, game)
        return room, game, None

    def _check_winner(self, state):
        lines = state + [list(col) for col in zip(*state)]
        lines.append([state[i][i] for i in range(3)])
        lines.append([state[i][2-i] for i in range(3)])
        for line in lines:
            if line[0] and all(cell == line[0] for cell in line): return line[0]
        if all(cell for row in state for cell in row): return "Empate"
        return None
