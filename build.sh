#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "🚀 Starting build process..."

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🗂️ Collecting static files..."
python manage.py collectstatic --no-input

echo "🔄 Running database migrations..."
python manage.py migrate

echo "✅ Build completed successfully!"