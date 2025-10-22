from datetime import datetime

class SessionRepository:
    def __init__(self, db):
        self.sessions = db["sessions"]

    def create(self, user_id, token):
        # Remove sessão antiga se existir, para garantir uma por usuário
        self.sessions.delete_one({"user_id": user_id})
        session = {"user_id": user_id, "token": token, "created_at": datetime.utcnow()}
        self.sessions.insert_one(session)
        return session

    def delete(self, token):
        result = self.sessions.delete_one({"token": token})
        return result.deleted_count > 0
    
    def get_by_user(self, user_id):
        return self.sessions.find_one({"user_id": user_id})
    
    def get_by_token(self, token):
        """Retorna a sessão pelo token"""
        return self.sessions.find_one({"token": token})

    def get_all_sessions(self):
        return list(self.sessions.find())
