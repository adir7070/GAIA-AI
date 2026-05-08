"""All ORM models. Importing this module registers them with the metadata."""
from app.db.models.contact import Contact
from app.db.models.feedback import Feedback
from app.db.models.permission import Permission
from app.db.models.session import Session
from app.db.models.user import User

all_models = [User, Session, Contact, Permission, Feedback]

__all__ = ["User", "Session", "Contact", "Permission", "Feedback", "all_models"]
