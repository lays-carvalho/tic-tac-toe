from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.repositories.session_repository import SessionRepository
from app.services.room_service import RoomService
from app.utils.auth_decorator import token_required
from app import db

auth_bp = Blueprint("auth", __name__)
user_service = UserService(UserRepository(db))
room_service = RoomService(db)
session_repo = SessionRepository(db)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    auth_data = user_service.authenticate(username, password)
    if not auth_data:
        error_message = "Usuário ou senha inválidos. Tente novamente."
        return render_template("login.html", error=error_message)

    user_id = auth_data["user_id"]
    token = auth_data["token"]
    
    session_repo.create(user_id, token)
    
    response = redirect(url_for("lobby"))
    response.set_cookie("token", token, httponly=True, max_age=60 * 60 * 24 * 30)
    return response

@auth_bp.route("/logout", methods=["POST"])
@token_required()
def logout(current_user):
    token = request.cookies.get("token")
    if token:
        session_repo.delete(token)

    try:
        room_service.leave_room(str(current_user["_id"]), current_user["username"])
    except Exception as e:
        print(f"Erro ao remover jogador das salas no logout: {e}")

    response = redirect(url_for("auth.login"))
    response.delete_cookie("token")
    return response