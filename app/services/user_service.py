import jwt
from werkzeug.security import check_password_hash
from flask import current_app

class UserService:
    def __init__(self, user_repository):
        self.user_repo = user_repository

    def register(self, username, password, is_admin=False):
        existing = self.user_repo.find_by_username(username)
        if existing:
            return {"error": "Usuário já existe"}
        user = self.user_repo.create(username, password, is_admin=is_admin)
        user.pop("password", None)
        return {"message": "Usuário criado com sucesso", "user": user}

    def authenticate(self, username, password):
        user = self.user_repo.find_by_username(username)
        if user and check_password_hash(user["password"], password):
            user_id = str(user["_id"])

            token_payload = {
                "user_id": user_id,
                "username": user["username"],
                "is_admin": user.get("is_admin", False)
            }
            
            token = jwt.encode(token_payload, current_app.config["SECRET_KEY"], algorithm="HS256")

            
            return {
                "user_id": user_id,
                "username": user["username"],
                "is_admin": user.get("is_admin", False),
                "token": token
            }

        return None

    def get_all(self):
        users = self.user_repo.find_all()
        for u in users:
            u["_id"] = str(u["_id"])
        return users

    def get_by_id(self, id):
        user = self.user_repo.find_by_id(id)
        if user:
            user["_id"] = str(user["_id"])
            user.pop("password", None)
            return user
        return None

    def update(self, id, data):
        success = self.user_repo.update(id, data)
        if not success:
            return {"error": "Usuário não encontrado ou dados iguais"}
        return {"message": "Usuário atualizado com sucesso"}

    def delete(self, id):
        success = self.user_repo.delete(id)
        if not success:
            return {"error": "Usuário não encontrado"}
        return {"message": "Usuário deletado com sucesso"}