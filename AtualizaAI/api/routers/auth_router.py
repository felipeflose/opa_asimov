import os
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from api.auth import create_access_token
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/auth", tags=["Security"])

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    admin_email: str
    status: str

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Realiza o login administrativo e retorna um JWT v3"""
    # Credenciais via .env (seguro via Secret Manager em produção)
    expected_email = os.getenv("ADMIN_EMAIL")
    expected_key = os.getenv("MASTER_KEY")

    if req.email == expected_email and req.password == expected_key:
        token = create_access_token(req.email)
        logger.info("login_success", email=req.email)
        return LoginResponse(
            token=token,
            admin_email=req.email,
            status="authorized"
        )
    
    logger.warn("login_failed", email=req.email)
    raise HTTPException(status_code=401, detail="E-mail ou senha mestra inválidos")
