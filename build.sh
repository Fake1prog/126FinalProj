#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "🚀 Starting build process..."

echo "🐍 Python version:"
python --version

echo "📦 Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🔍 Verifying PostgreSQL adapter..."
python -c "
try:
    import psycopg2
    print('✅ psycopg2-binary installed successfully')
except ImportError as e:
    print(f'❌ psycopg2 import failed: {e}')
    print('🔄 Installing psycopg2-binary manually...')
    import subprocess
    subprocess.run(['pip', 'install', 'psycopg2-binary==2.9.9'], check=True)
    import psycopg2
    print('✅ psycopg2-binary manual installation successful')
"

echo "🗂️ Collecting static files..."
# Use --ignore-missing-deps to skip missing file references
python manage.py collectstatic --no-input --clear

echo "🔄 Running database migrations..."
python manage.py migrate

echo "✅ Build completed successfully!"