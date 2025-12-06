#!/usr/bin/env python3
"""
Script to create the scrimgg database on RDS PostgreSQL.
Run this from your local machine or from a Python environment with psycopg2-binary.
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connection details - connect to 'postgres' database first
DATABASE_URL = "postgresql://postgres:postgres15982@scrimggdbpg.chf7ujytuaf8.us-east-2.rds.amazonaws.com:5432/postgres?sslmode=require"

def create_database():
    """Create the scrimgg database if it doesn't exist."""
    try:
        # Connect to postgres database
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = 'scrimgg'"
        )
        exists = cursor.fetchone()
        
        if exists:
            print("Database 'scrimgg' already exists.")
        else:
            # Create database
            print("Creating database 'scrimgg'...")
            cursor.execute('CREATE DATABASE scrimgg')
            print("Database 'scrimgg' created successfully!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    create_database()

