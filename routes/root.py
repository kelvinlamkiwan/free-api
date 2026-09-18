from fastapi import APIRouter

from handlers import RootHandler


router = APIRouter()
handler = RootHandler()


@router.get("/")
def root():
    return handler.get_message()
