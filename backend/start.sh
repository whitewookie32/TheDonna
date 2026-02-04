#!/bin/bash
# The Donna - Railway Start Script

cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
