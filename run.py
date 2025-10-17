from app import create_app, socketio

app_instance = create_app()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    socketio.run(
        app_instance,
        host="0.0.0.0",
        port=port,
        debug=True,
        use_reloader=False
    )
