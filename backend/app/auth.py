import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import settings

security = HTTPBasic()


def require_hr(credentials: HTTPBasicCredentials = Depends(security)):
    """Let the request through only with the HR username and password."""
    correct_user = secrets.compare_digest(credentials.username, settings.hr_username)
    correct_password = secrets.compare_digest(credentials.password, settings.hr_password)
    if not (correct_user and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong username or password",
            headers={"WWW-Authenticate": "Basic"},
        )