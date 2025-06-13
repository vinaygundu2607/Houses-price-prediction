from waitress import serve
from app import app
import os

if __name__ == '__main__':
    # Get port from environment variable or default to 8000
    port = int(os.environ.get('PORT', 8000))
    
    print(f"Starting server on port {port}...")
    print(f"You can access the application at http://localhost:{port}")
    print("Press Ctrl+C to quit")
    
    serve(app, host='0.0.0.0', port=port, threads=4) 