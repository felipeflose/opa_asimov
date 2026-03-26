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
    expected_email = os.getenv("ADMIN_EMAIL", "").strip()
    expected_key = os.getenv("MASTER_KEY", "").strip()

    req_email = req.email.strip()
    req_pass = req.password.strip()

    if req_email == expected_email and req_pass == expected_key:
        token = create_access_token(req_email)
        logger.info("login_success", email=req_email)
        return LoginResponse(
            token=token,
            admin_email=req_email,
            status="authorized"
        )
    
    # Log de diagnóstico (seguro, não exponha a senha crua)
    logger.warn("login_failed", 
                tried_email=req_email, 
                expected_config_email_starts_with=expected_email[:4] if expected_email else "MISSING",
                pass_len=len(req_pass),
                expected_pass_len=len(expected_key))
    
    raise HTTPException(status_code=401, detail="E-mail ou senha mestra inválidos")
