from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from contextlib import asynccontextmanager

from sqlmodel import Session
from .database import get_db, create_db_and_tables, check_database_tables

from . import utils
from topazdevsdk import colors
from . import schemas, crud
from .routes_users import router as users_router


################# App Initialization #################

@asynccontextmanager
async def lifespan(app_: FastAPI):
    # Démarrage de l'application
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     -------------------")
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     {colors.BColors.PURPLE}{utils.CONFIG['api']['name']}{colors.BColors.END}")
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     Version {colors.BColors.LIGHTBLUE}{utils.VERSION}{colors.BColors.END}")
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     -------------------")
    
    # Initialisation de la base de données
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     Initialisation de la base de données...")
    create_db_and_tables()
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     Base de données initialisée.")
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     -------------------")
    
    # Vérification des tables de la base de données existantes par rapport aux modèles
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     Vérification des tables de la base de données...")
    check_database_tables()
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     Vérification terminée.")
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     -------------------")
    
    # Initialisation de la sécurité
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     Initialisation de la sécurité...")
    db = next(get_db())
    result = crud.loadsecurity(db, utils.SECURITY)
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     Sécurité initialisée. Résultat: {result.get('result') if result.get('result') is not None else result.get('erreur', 'Erreur inconnue')}")
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     -------------------")

    # Fonctionnement de l'application
    yield
    
    # Arrêt de l'application
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     -------------------")
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     Arrêt en cours...")

# Paramétrage de l'application FastAPI
app = FastAPI(
    title=utils.CONFIG['api']['name'],
    version=utils.VERSION,
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan
)

################# Templates #################

templates = Jinja2Templates(directory="templates")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

favicon_path = 'assets/images/favicon.ico'
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)

################# Security #################

# -----------------------------------------------
@app.post("/token", tags=["Security"])
async def secu_login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    """
    Authentification OAuth2
    """
    # # Vérifier le client_id et client_secret
    # if utils.CLIENT_ID and utils.CLIENT_SECRET:
    #     client_id = form_data.client_id if form_data.client_id else None
    #     client_secret = form_data.client_secret if form_data.client_secret else None

    #     if not client_id or client_id != utils.CLIENT_ID:
    #         raise HTTPException(status_code=400, detail="Invalid client_id")
    #     if not client_secret or client_secret != utils.CLIENT_SECRET:
    #         raise HTTPException(status_code=400, detail="Invalid client_secret")
    
    # Vérifier les credentials de l'utilisateur
    user_dict = crud.secu_get_user_by_username(db, form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    hashed_password = crud.hash_password(form_data.password)
    if not hashed_password == user_dict.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user_dict.username, "token_type": "bearer"}

# -----------------------------------------------
@app.get("/security/me", tags=["Security"])
async def read_securityusers_me(current_user: Annotated[schemas.Users, Depends(crud.secu_get_current_active_user)], db: Session = Depends(get_db)):
    return JSONResponse(content=jsonable_encoder(current_user))

################# Include Routers #################

app.include_router(users_router)

################# Main Routes #################

# -----------------------------------------------
@app.get("/", response_class=HTMLResponse)
def html_main(request: Request):
    return templates.TemplateResponse("landing.html", {
        "request": request, 
        "name": utils.CONFIG['api']['name'],
        "version": utils.VERSION, 
        "hostname": utils.HOSTNAME
    })

# -----------------------------------------------
@app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    swagger_ui = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{utils.CONFIG['api']['name']} - Documentation",
        swagger_favicon_url="/assets/images/favicon.ico"
    )
    return templates.TemplateResponse("docs.html", {
        "request": request, 
        "name": utils.CONFIG['api']['name'],
        "version": utils.VERSION,
        "hostname": utils.HOSTNAME,
        "swagger_ui_html": swagger_ui.body.decode()
    })

# -----------------------------------------------
@app.get("/redoc", response_class=HTMLResponse, include_in_schema=False)
async def redoc_html(request: Request):
    redoc_ui = get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{utils.CONFIG['api']['name']} - ReDoc Documentation",
        redoc_favicon_url="/assets/images/favicon.ico"
    )
    return templates.TemplateResponse("redoc.html", {
        "request": request, 
        "name": utils.CONFIG['api']['name'],
        "version": utils.VERSION,
        "hostname": utils.HOSTNAME,
        "redoc_ui_html": redoc_ui.body.decode()
    })

# -----------------------------------------------
@app.get("/api/version/")
def app_version():
    result = {'name': utils.CONFIG['api']['name'], 'version': utils.CONFIG['api']['version']}
    return JSONResponse(content=jsonable_encoder(result))

