from .pdf import router as pdf_router
from .root import router as root_router

routers = [root_router, pdf_router]

__all__ = ["routers"]
