from website import create_app

app = create_app()

if __name__ == '__main__':
    # WARNING: Only use this for development
    # For production, use a proper WSGI server like Gunicorn
    app.run(host='0.0.0.0', port=8000, debug=False)