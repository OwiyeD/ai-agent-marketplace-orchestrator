# scripts/migrate.sh - Database migration script
#!/bin/bash
set -e

echo "🔄 Running database migrations..."

# Check if database is accessible
if ! pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not accessible. Make sure it's running."
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Initialize Alembic if not already done
if [ ! -f alembic.ini ]; then
    echo "📝 Initializing Alembic..."
    poetry run alembic init migrations
fi

# Create migration if schema changes detected
echo "🔍 Checking for schema changes..."
poetry run alembic revision --autogenerate -m "Auto-migration $(date +'%Y%m%d_%H%M%S')"

# Apply migrations
echo "⬆️  Applying migrations..."
poetry run alembic upgrade head

# Verify migration
echo "✅ Verifying migration..."
poetry run alembic current

echo "✅ Database migrations completed successfully"