import os
from flask import Flask, render_template, request, redirect, url_for, g
from flask_socketio import SocketIO
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

from app.services.user_service import UserService
from app.services.room_cleanup import start_cleanup_scheduler
from app.repositories.user_repository import UserRepository
from app.repositories.session_repository import SessionRepository

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")
MONGO_URI = os.getenv("MONGO_URI")

socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")

# --- Conexão com MongoDB ---
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')
    db = mongo_client["jala_tic-toc-toe"]
    print("✅ Conexão com MongoDB Atlas OK!")
except ConnectionFailure as e:
    print("❌ Erro ao conectar no MongoDB Atlas:", e)
    db = None

# --- Instancia repositórios ---
session_repo = SessionRepository(db)
user_repo = UserRepository(db)

def create_app():
    app = Flask(
        __name__,
        template_folder="frontend/templates",
        static_folder="frontend/static"
    )
    app.config["SECRET_KEY"] = SECRET_KEY
    app.debug = True
    socketio.init_app(app)

    from app.controllers.auth_controller import auth_bp
    from app.controllers.user_controller import user_bp
    from app.controllers.room_controller import room_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(room_bp)

    # --- Antes de cada request: define usuário atual ---
    @app.before_request
    def load_current_user():
        token = request.cookies.get("token")
        g.current_user = None
        if token:
            session = session_repo.get_by_token(token)
            if session:
                user_id = session["user_id"]
                g.current_user = user_repo.find_by_id(user_id)  # pega o usuário completo


    # --- Rotas públicas ---
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/signup")
    def signup():
        return render_template("signup.html")

    @app.route("/lobby")
    def lobby():
        if not g.current_user:
            return redirect(url_for("auth.login"))
        return render_template("lobby.html", current_user=g.current_user)

    @app.route("/game")
    def game():
        if not g.current_user:
            return redirect(url_for("auth.login"))
        return render_template("game.html")

    @app.route("/ranking")
    def ranking():
        return render_template("ranking.html")

    @app.route("/monitor")
    def monitor():
        if not g.current_user or g.current_user.get("username") != "admin":
            return redirect(url_for("auth.login"))
        return render_template("monitor.html")

    # --- Socket ---
    from app.sockets.game_socket import register_game_events
    register_game_events(socketio, db)

    # --- Inicialização ---
    if db is not None:
        start_cleanup_scheduler(db)
        if not user_repo.find_by_username("admin"):
            user_repo.create("admin", "admin123", is_admin=True)
            print("✅ Usuário admin criado (login: admin / senha: admin123)")


    return app
