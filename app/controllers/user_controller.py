from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.repositories.session_repository import SessionRepository
from app.utils.auth_decorator import token_required
from app.utils.mongo_utils import convert_objectid
from app import db

user_bp = Blueprint("users", __name__)
user_service = UserService(UserRepository(db))
session_repo = SessionRepository(db)

def user_summary(user):
    return {"id": str(user["_id"]), "username": user["username"]}

@user_bp.route("/users/me", methods=["GET"])
@token_required()
def get_me(current_user):
    return jsonify(convert_objectid(current_user))

@user_bp.route("/users/online", methods=["GET"])
@token_required()
def get_online_users(current_user):
    sessions = session_repo.get_all_sessions()
    result = []
    for s in sessions:
        user = user_service.get_by_id(s["user_id"])
        if user and not user.get("is_admin", False) and str(user["_id"]) != str(current_user["_id"]):
            result.append(user_summary(user))
    return jsonify(result)

@user_bp.route("/users", methods=["POST"])
def create_user():
    username = request.form.get("username")
    password = request.form.get("password")
    if not username or not password:
        return render_template("signup.html", error="Usuário e senha são obrigatórios.")

    result = user_service.register(username, password)
    if "error" in result:
        return render_template("signup.html", error="Este nome de usuário já está em uso. Tente outro.")
    return redirect(url_for("auth.login"))

@user_bp.route("/users/me", methods=["DELETE"])
@token_required()
def delete_me(current_user):
    user_id = str(current_user["_id"])
    result = user_service.delete(user_id)
    if "error" in result:
        return jsonify(result), 404
    
    token = request.cookies.get("token")
    if token:
        session_repo.delete(token)
    
    response = jsonify({"message": "Conta deletada com sucesso"})
    response.delete_cookie('token') 
    return response

# Rotas de admin
# --- Retorna todos os usuários cadastrados (apenas admin) ---
@user_bp.route("/users/all", methods=["GET"])
@token_required(admin_only=True)
def get_all_users(current_user):
    users = user_service.get_all()  # <--- aqui
    result = [{"id": u["_id"], "username": u["username"]} for u in users]
    return jsonify(result)

@user_bp.route("/users/<id>", methods=["DELETE"])
@token_required(admin_only=True)
def delete_user(current_user, id):
    result = user_service.delete(id)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)

@user_bp.route("/ranking-data", methods=["GET"])
def get_ranking_data():
    # Busca todos os usuários
    users = user_service.get_all()
    
    # Filtra usuários que não são admin
    players = [u for u in users if not u.get("is_admin", False)]
    
    # Ordena os jogadores: vitórias (maior para menor), depois derrotas (menor para maior)
    sorted_players = sorted(
        players, 
        key=lambda p: (p.get("stats", {}).get("wins", 0), -p.get("stats", {}).get("losses", 0)), 
        reverse=True
    )
    
    return jsonify(sorted_players)