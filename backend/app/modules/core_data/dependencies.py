"""Dependencies for core_data domain."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.core_data.services.users import UserService
from app.modules.core_data.repositories.users import UserRepository


def get_user_service(session: Session = Depends(get_db)) -> UserService:
    """Get user service dependency."""
    return UserService(session)

def get_user_repo(session: Session = Depends(get_db)):
    """Get user repository dependency."""
    return UserRepository(session)
