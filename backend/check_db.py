from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Set python path to find 'app'
sys.path.append(os.getcwd())

from app.database import Base
from app.models.user import User
from app.models.document import Document
from app.models.query import QueryRecord
from app.models.audit import AuditLog

engine = create_engine("sqlite:///app.db")
Session = sessionmaker(bind=engine)
session = Session()

try:
    users = session.query(User).all()
    print(f"Users in DB: {len(users)}")
    for u in users:
        print(f"- {u.email} ({u.role.value})")
except Exception as e:
    print(f"Error querying DB: {e}")
