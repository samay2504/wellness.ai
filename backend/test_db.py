import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path

app = Flask(__name__)

# Use the database directly in current directory  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wellness.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

with app.app_context():
    try:
        # Try to connect to database
        with db.engine.connect() as conn:
            result = conn.execute(db.text('SELECT 1'))
            print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {e}")
