import os
if os.path.exists("app.db"):
    try:
        os.remove("app.db")
    except:
        pass

from app.database import engine, Base
from app.models.user import User
from app.models.document import Document
from app.models.query import QueryRecord
from app.models.audit import AuditLog
from app.models.document_version import DocumentVersion
from app.models.conversation import Conversation, ConversationMessage
from app.models.webhook import WebhookSubscription

Base.metadata.create_all(bind=engine)

from sqlalchemy.orm import Session
with Session(engine) as session:
    admin = User(
        email="admin@example.com",
        full_name="admin",
        hashed_password="hashed_password",
        role="admin"
    )
    session.add(admin)
    session.commit()
