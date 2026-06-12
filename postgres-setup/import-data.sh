#!/bin/bash
set -e

echo "Starting PostgreSQL data restoration..."

# Check if dvdrental database already exists
if psql -U "$POSTGRES_USER" -tc "SELECT 1 FROM pg_database WHERE datname = 'dvdrental'" | grep -q 1; then
    echo "dvdrental database already exists, skipping creation."
else
    echo "Creating dvdrental database..."
    createdb -U "$POSTGRES_USER" dvdrental
fi

# Restore the data from the tar file
echo "Restoring data from dvdrental.tar..."
pg_restore -U "$POSTGRES_USER" -d dvdrental --no-owner --no-privileges /tmp/dvdrental.tar

echo "Data restoration completed successfully!"