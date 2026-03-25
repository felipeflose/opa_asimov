import os
import time
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

logger = structlog.get_logger()

# Configurações de Segurança
# SECRET_KEY preferencialmente do GCP Secret Manager, fallback .env
SECRET_KEY = os.getenv("MASTER_KEY", "fallback_local_secret_v3_change_asap")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 12

security = HTTPBearer()

class AuthError(Exception):
    pass

def create_access_token(admin_email: str) -> str:
    """Gera o JWT para o admin_email fornecido"""
    expires = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": admin_email,
        "exp": expires,
        "iat": datetime.utcnow()
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def require_auth(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Middleware/Dependency para validar o JWT nos routers do FastAPI"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_email = payload.get("sub")
        
        if admin_email is None:
            raise HTTPException(status_code=401, detail="Token inválido: subject ausente")
        
        # Expiração é validada pelo jwt.decode se 'exp' estiver no payload
        return admin_email
    except JWTError as e:
        logger.warn("auth_failed", error=str(e))
        raise HTTPException(status_code=401, detail=f"Token inválido ou expirado: {str(e)}")

# Helper para verificação simples sem Dependency (se necessário em Webhooks)
def validate_token_raw(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except:
        return None
