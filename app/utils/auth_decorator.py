import jwt
from functools import wraps
from flask import request, jsonify, current_app
from app.repositories.user_repository import UserRepository
from app import db

user_repo = UserRepository(db)

def token_required(admin_only=False):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = None
            
            
            if "Authorization" in request.headers:
                parts = request.headers["Authorization"].split()
                if len(parts) == 2 and parts[0] == "Bearer":
                    token = parts[1]

            
            if not token:
                token = request.cookies.get('token')

            if not token:
                return jsonify({"error": "Token ausente"}), 401

            try:
                data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
                user = user_repo.find_by_id(data["user_id"])
                if not user:
                    return jsonify({"error": "Usuário não existe"}), 404
                if admin_only and not data.get("is_admin", False):
                    return jsonify({"error": "Permissão negada"}), 403
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expirado"}), 401
            except Exception:
                return jsonify({"error": "Token inválido"}), 401

            return f(user, *args, **kwargs)
        return wrapper
    return decorator
