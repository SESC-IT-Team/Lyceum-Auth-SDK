from fastapi import APIRouter

router = APIRouter(prefix="/auth")

@router.post("/token", response_model=schemas.Token)
