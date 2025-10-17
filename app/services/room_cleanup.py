import threading
from datetime import datetime, timedelta
from app.services.room_service import RoomService

INTERVAL = 300  # 5 minutos

def start_cleanup_scheduler(db):
    room_service = RoomService(db)

    def run_cleanup():
        try:
            room_service.mark_empty_rooms_inactive()
            cleanup_inactive_rooms(room_service)
        finally:
            threading.Timer(INTERVAL, run_cleanup).start()

    threading.Timer(INTERVAL, run_cleanup).start()
    print(" - Agendador de limpeza de salas iniciado. -")

def cleanup_inactive_rooms(room_service, minutes_inactive=30):
    rooms = room_service.repo.get_all()
    now = datetime.utcnow()
    for room in rooms:
        last_activity = room.get("last_activity")
        if room.get("status") == "Inativa" and last_activity:
            if now - last_activity > timedelta(minutes=minutes_inactive):
                print(f"🗑 Deletando sala inativa {room['_id']}")
                room_service.repo.delete_room(str(room["_id"]))