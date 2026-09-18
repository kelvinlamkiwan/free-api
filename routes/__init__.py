from .barcode import router as barcode_router
from .image import router as image_router
from .pdf import router as pdf_router
from .qrcode import router as qrcode_router
from .root import router as root_router
from .utils import router as utils_router

routers = [root_router, pdf_router, image_router, qrcode_router, barcode_router, utils_router]

__all__ = ["routers"]
