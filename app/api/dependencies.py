from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.config import settings
import jwt
from datetime import datetime, timedelta
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
redis_client = redis.from_url(settings.redis_url)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Validate JWT token and return current user"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
        
    result = await db.execute(
        "SELECT * FROM users WHERE id = :id",
        {"id": user_id}
    )
    user = result.first()
    
    if user is None:
        raise credentials_exception
    return user

async def rate_limit(request: Request):
    """Rate limiting middleware"""
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"
    
    try:
        current = await redis_client.get(key)
        if current and int(current) >= settings.rate_limit_requests:
            raise HTTPException(
                status_code=429,
                detail="Too many requests"
            )
            
        pipe = redis_client.pipeline()
        await pipe.incr(key)
        await pipe.expire(key, settings.rate_limit_period)
        await pipe.execute()
        
    except redis.RedisError as e:
        logger.error(f"Redis error in rate limiting: {str(e)}")
        # Continue without rate limiting if Redis is down
        pass

async def check_api_key(request: Request):
    """Validate API key for external requests"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is required"
        )
        
    try:
        result = await redis_client.get(f"api_key:{api_key}")
        if not result:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
    except redis.RedisError as e:
        logger.error(f"Redis error in API key validation: {str(e)}")
        # Continue without API key validation if Redis is down
        pass

def create_access_token(
    data: dict,
    expires_delta: timedelta = None
):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt