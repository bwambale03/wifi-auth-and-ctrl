from app import create_app, register_commands
import os

if __name__ == "__main__":
    app = create_app()
    register_commands(app)

    # Determine environment (development or production)
    env = os.getenv('FLASK_ENV', 'development')
    port = int(os.getenv('PORT', 5000))

    if env == 'production':
        # Use a production WSGI server like Waitress
        from waitress import serve
        print(f"Starting production server on port {port}...")
        serve(app, host='0.0.0.0', port=port)
    else:
        # Run Flask's built-in server for development
        print(f"Starting development server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=True)
    