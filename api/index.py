import sys
import os

# Resolve paths so backend and project root are in sys.path for Vercel Serverless Function
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.app import app

# Vercel serverless function entrypoint
handler = app
