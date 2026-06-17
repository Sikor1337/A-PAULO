from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.dependencies import _sql_engine
from app.core.errors import register_error_handlers
from app.infrastructure.sql.base import Base
from app.infrastructure.sql import models_registry  # noqa: F401 - Register all models
from app.modules.core_data.api.roles import router as roles_router
from app.modules.security.api import router as security_router
from app.modules.pi.api.volunteers import router as volunteers_router
from app.modules.pi.api.beneficiaries import router as beneficiaries_router
from app.modules.pi.api.groups import router as groups_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Tables are managed by Alembic migrations.
    yield
app = FastAPI(
    title="PaPka",
    version="1.0.0",
    lifespan=lifespan,

)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")


# Auth endpoints (no /api/v1 prefix for backward compatibility)
app.include_router(security_router)

# API v1 endpoints
app.include_router(roles_router, prefix="/api/v1")
app.include_router(volunteers_router, prefix="/api/v1")
app.include_router(beneficiaries_router, prefix="/api/v1")
app.include_router(groups_router, prefix="/api/v1")

