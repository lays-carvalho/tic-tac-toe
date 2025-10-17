# Apenas representação dos dados
class Match:
    def __init__(self, player_x, player_o):
        self.player_x = player_x
        self.player_o = player_o
        self.state = [["" for _ in range(3)] for _ in range(3)]
        self.turn = "X"
        self.winner = None
