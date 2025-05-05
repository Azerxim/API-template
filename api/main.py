import os
from typing import List
from fastapi import Depends, FastAPI, HTTPException, Security, Request, status
from fastapi.security.api_key import APIKeyHeader, APIKey
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from topazdevsdk import file as f, colors
from . import crud, models, schemas
from .database import SessionLocal, engine

# CONFIGURATION
path = f"{os.path.realpath(os.path.dirname(__file__))}/../config/"
pathfile = f"{path}config.json"

if not f.exist(path):
	f.createdir(path)

if not f.exist(pathfile):
	f.create(pathfile)
	data = '{"version": "1.1", "name": "DB API", "key": "INSERT PRIVATE KEY HERE"}'
	f.write(pathfile, data)


models.Base.metadata.create_all(bind=engine)


app = FastAPI()
CONFIG = f.json_read("config/config.json")
VERSION = CONFIG['version']
NAME = CONFIG['name']
SECRET_KEY = CONFIG['key']
SECRET_KEY_NAME = "access_token"


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

################# Templates ####################

templates = Jinja2Templates(directory="html")


################# Security #####################

api_key_header = APIKeyHeader(name=SECRET_KEY_NAME)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == SECRET_KEY:
        return api_key_header
    else:
        raise HTTPException(status_code=403, detail="Could not validate credentials")


################### API ########################
@app.on_event("startup")
async def startup_event():
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     -------------------")
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     {colors.BColors.PURPLE}{NAME}{colors.BColors.END}")
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     Version {colors.BColors.LIGHTBLUE}{VERSION}{colors.BColors.END}")
    print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     -------------------")


@app.get("/", response_class=HTMLResponse)
def html_main(request: Request):
    return templates.TemplateResponse("version.html", {"request": request, "api": NAME, "version": VERSION})


@app.get("/version/")
def app_version():
    return {'api': NAME, 'version': VERSION}


# --------------------------------------
# ---------------- HTML ----------------
# --------------------------------------

# ==== ERROR ====
@app.get("/error-404", response_class=HTMLResponse)
def app_error(request: Request):
    return templates.TemplateResponse("error-404.html", {"request": request, "api": NAME})

@app.get("/error", response_class=HTMLResponse)
def error(request: Request, text: str):
    return templates.TemplateResponse("error.html", {"request": request, "api": NAME, "text": text})


# ==== READ ====
@app.get("/html/users/read/", response_class=HTMLResponse, tags=["HTML"])
def html_read_users(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db=db, skip=skip, limit=limit)
    return templates.TemplateResponse("users.html", {"request": request, "api": NAME, "users": users})

@app.get("/html/user/read/{PlayerID}", response_class=HTMLResponse, tags=["HTML"])
def html_read_user(request: Request, PlayerID: int, db: Session = Depends(get_db)):
    user = crud.get_user(db=db, PlayerID=PlayerID)
    if user is None:
        return templates.TemplateResponse("error.html", {"request": request, "api": NAME, "text": "Utilisateur non trouvé"})
    return templates.TemplateResponse("user.html", {"request": request, "api": NAME, "user": user})


# ========= Info Global =========
@app.get("/infos/", tags=["Infos"])
def read_global_info(db: Session = Depends(get_db)):
    infos = {}
    # Devise
    res = crud.countTotalDevise(db=db)
    if res is None:
        res = {}
    infos['Devise'] = res
    # Super Devise
    res = crud.countTotalSuperDevise(db=db)
    if res is None:
        res = {}
    infos['Super Devise'] = res
    # Taille
    res = crud.taille(db=db)
    if res is None:
        res = {}
    infos['Total Players'] = res
    return JSONResponse(content=jsonable_encoder(infos))


@app.get("/infos/devise/", tags=["Infos"])
def read_global_devise(db: Session = Depends(get_db)):
    res = crud.countTotalDevise(db=db)
    if res is None:
        res = {}
    return JSONResponse(content=jsonable_encoder(res))


@app.get("/infos/super_devise/", tags=["Infos"])
def read_global_super_devise(db: Session = Depends(get_db)):
    res = crud.countTotalSuperDevise(db=db)
    if res is None:
        res = {}
    return JSONResponse(content=jsonable_encoder(res))


@app.get("/infos/nb_player/", tags=["Infos"])
def get_nb_player(db: Session = Depends(get_db)):
    res = crud.taille(db=db)
    if res is None:
        raise HTTPException(status_code=400, detail="Database not found")
    return res


# ========= Users =========
@app.get("/users/playerid/{discord_id}", tags=["Users"])
def get_playerID(discord_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_PlayerID(db=db, discord_id=discord_id, platform="discord")
    if db_user is None:
        res = {'error': 404, 'ID': 0}
    else:
        res = {'error': 0, 'ID': "{}".format(db_user.playerid)}
    return JSONResponse(content=jsonable_encoder(res))


@app.post("/users/", response_model=schemas.TableCore, tags=["Users"])
def create_user(user: schemas.TableCore, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    db_user = crud.get_user_discord_id(db, discord_id=user.discord_id)
    if db_user:
        raise HTTPException(status_code=400, detail="Discord ID already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[schemas.TableCore], tags=["Users"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db=db, skip=skip, limit=limit)
    return users


@app.get("/users/{PlayerID}", response_model=schemas.TableCore, tags=["Users"])
def read_user(PlayerID: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db=db, PlayerID=PlayerID)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# ----- Devise -----
@app.get("/users/devise/{PlayerID}", tags=["Users"])
def user_devise(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "devise")
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content=jsonable_encoder(val))


@app.put("/users/devise/{PlayerID}/{nb}", tags=["Users"])
def add_devise(PlayerID: int, nb: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        lang = crud.value(db, PlayerID, "core", "lang")
        bal = crud.value(db, PlayerID, "core", "devise")
        ns = bal + int(nb)
        if ns <= 0:
            ns = 0
        crud.update(db, PlayerID, "core", "devise", ns)
        func = {'error': 0, 'etat': 'OK', 'lang': lang, 'newvalue': ns, 'oldvalue': bal}
    except:
        func = {'error': 1, 'etat': 'NOK', 'lang': lang}
    return JSONResponse(content=jsonable_encoder(func))


# ----- Super Devise -----
@app.get("/users/super_devise/{PlayerID}", tags=["Users"])
def user_super_devise(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "super_devise")
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content=jsonable_encoder(val))


@app.put("/users/super_devise/{PlayerID}/{nb}", tags=["Users"])
def add_super_devise(PlayerID: int, nb: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        lang = crud.value(db, PlayerID, "core", "lang")
        bal = crud.value(db, PlayerID, "core", "super_devise")
        ns = bal + int(nb)
        if ns <= 0:
            ns = 0
        crud.update(db, PlayerID, "core", "super_devise", ns)
        func = {'error': 0, 'etat': 'OK', 'lang': lang, 'newvalue': ns, 'oldvalue': bal}
    except:
        func = {'error': 1, 'etat': 'NOK', 'lang': lang}
    return JSONResponse(content=jsonable_encoder(func))


# ----- Level -----
@app.get("/users/level/{PlayerID}", tags=["Users"])
def user_level(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "level")
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content=jsonable_encoder(val))


@app.put("/users/level/{PlayerID}/{nb}", tags=["Users"])
def add_level(PlayerID: int, nb: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        lang = crud.value(db, PlayerID, "core", "lang")
        bal = crud.value(db, PlayerID, "core", "level")
        ns = bal + int(nb)
        if ns <= 0:
            ns = 0
        crud.update(db, PlayerID, "core", "level", ns)
        func = {'error': 0, 'etat': 'OK', 'lang': lang, 'newvalue': ns, 'oldvalue': bal}
    except:
        func = {'error': 1, 'etat': 'NOK', 'lang': lang}
    return JSONResponse(content=jsonable_encoder(func))


# ----- XP -----
@app.get("/users/xp/{PlayerID}", tags=["Users"])
def user_xp(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "xp")
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content=jsonable_encoder(val))


@app.put("/users/xp/{PlayerID}/{nb}", tags=["Users"])
def add_xp(PlayerID: int, nb: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        lang = crud.value(db, PlayerID, "core", "lang")
        bal = crud.value(db, PlayerID, "core", "xp")
        ns = bal + int(nb)
        if ns <= 0:
            ns = 0
        crud.update(db, PlayerID, "core", "xp", ns)
        func = {'error': 0, 'etat': 'OK', 'lang': lang, 'newvalue': ns, 'oldvalue': bal}
    except:
        func = {'error': 1, 'etat': 'NOK', 'lang': lang}
    return JSONResponse(content=jsonable_encoder(func))


# ----- Lang -----
@app.get("/users/lang/{PlayerID}", tags=["Users"])
def user_lang(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "lang")
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content=jsonable_encoder(val))


@app.put("/users/lang/{PlayerID}/{newLang}", tags=["Users"])
def update_lang(PlayerID: int, newLang: str, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        lang = crud.value(db, PlayerID, "core", "lang")
        newLang = newLang.upper()
        crud.update(db, PlayerID, "core", "lang", newLang)
        func = {'error': 0, 'etat': 'OK', 'lang': newLang, 'old': lang}
    except:
        func = {'error': 1, 'etat': 'NOK', 'lang': lang}
    return JSONResponse(content=jsonable_encoder(func))


# ----- Pseudo -----
@app.get("/users/pseudo/{PlayerID}", tags=["Users"])
def user_pseudo(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "pseudo")
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content=jsonable_encoder(val))


@app.put("/users/pseudo/{PlayerID}/{newUsername}", tags=["Users"])
def update_pseudo(PlayerID: int, newUsername: str, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    NU = newUsername
    pseudo = crud.value(db, PlayerID, "core", "pseudo")
    lang = crud.value(db, PlayerID, "core", "lang")
    func = {}
    if crud.in_table(db, "core", "pseudo", "pseudo", NU) is False:
        crud.update(db, PlayerID, "core", "pseudo", NU)
        crud.updateComTime(db, PlayerID, "update_pseudo")
        func = {'error': 0, 'etat': 'OK', 'lang': lang, 'new': NU, 'old': pseudo}
    else:
        func = {'error': 1, 'etat': 'NOK', 'lang': lang}
    return JSONResponse(content=jsonable_encoder(func))


# ----- Guild -----
@app.get("/users/guild/{PlayerID}", tags=["Users"])
def user_guild(PlayerID: int, db: Session = Depends(get_db)):
    val = crud.value(db, PlayerID, "core", "guild")
    if val is None:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(content=jsonable_encoder(val))


@app.put("/users/guild/{PlayerID}/{newGuild}", tags=["Users"])
def update_guild(PlayerID: int, newGuild: str, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    try:
        lang = crud.value(db, PlayerID, "core", "lang")
        guild = crud.value(db, PlayerID, "core", "guild")
        newGuild = newGuild.upper()
        crud.update(db, PlayerID, "core", "guild", newGuild)
        func = {'error': 0, 'etat': 'OK', 'lang': lang, 'new': newGuild, 'old': guild}
    except:
        func = {'error': 1, 'etat': 'NOK', 'lang': lang}
    return JSONResponse(content=jsonable_encoder(func))


# ----- Godchilds -----
@app.get("/users/godchilds/{PlayerID}", response_model=List[schemas.TableCore], tags=["Users"])
def get_godchilds(PlayerID: int, db: Session = Depends(get_db)):
    godchilds = crud.get_godchilds(db=db, PlayerID=PlayerID)
    if godchilds is None:
        return JSONResponse(content=jsonable_encoder({}))
    return godchilds


@app.put("/users/{PlayerID}/godparent/{godparentID}", response_model=schemas.TableCore, tags=["Users"])
def add_godparent(PlayerID: int, godparentID: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    lang = crud.value(db, PlayerID, "core", "lang")
    GPID = crud.get_PlayerID(db, godparentID, "discord")
    if GPID is None:
        func = {'error': 2, 'etat': 'NOK', 'lang': lang}
        return JSONResponse(content=jsonable_encoder(func))
    GPID = GPID.playerid
    myGP = crud.value(db, PlayerID, "core", "godparent")
    if (myGP == 0 or myGP == None or myGP is False) and PlayerID != GPID:
        crud.update(db, PlayerID, "core", "godparent", GPID)
        func = {'error': 0, 'etat': 'OK', 'lang': lang, 'new': GPID, 'old': myGP}
    else:
        func = {'error': 1, 'etat': 'NOK', 'lang': lang}
    return JSONResponse(content=jsonable_encoder(func))


# ========= Com Time =========
@app.get("/comtime/spam/{PlayerID}/{Command}/{couldown}", tags=["Command Time"])
def get_command_time(PlayerID: int, Command: str, couldown: int, db: Session = Depends(get_db)):
    res = crud.spam(db, PlayerID, couldown, Command)
    if res is None:
        res = {}
    return JSONResponse(content=jsonable_encoder(res))

@app.put("/comtime/update/{PlayerID}/{Command}", tags=["Command Time"])
def update_command_time(PlayerID: int, Command: str, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    res = crud.updateComTime(db, PlayerID, Command)
    if res is None:
        res = {}
    return JSONResponse(content=jsonable_encoder(res))


# ========= Test =========
# @app.post("/test/{PlayerID}", tags=["Test"])
# def test(PlayerID: int, db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
#     res = {}
#     if res is None:
#         res = {}
#     return JSONResponse(content=jsonable_encoder(res))
