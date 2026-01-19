from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
import hashlib

from . import models, schemas
from .database import get_db
from topazdevsdk import colors

################# Security #####################

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# -----------------------------------------------
async def secu_get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    user = secu_decode_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def secu_get_current_active_user(current_user: Annotated[schemas.Users, Depends(secu_get_current_user)]):
    if current_user.is_disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return JSONResponse(content=jsonable_encoder(current_user))

# -----------------------------------------------
def hash_password(password: str):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def secu_decode_token(db: Session, token):
    user = secu_get_user_by_username(db, token)
    return user

def secu_get_user_by_username(db: Session, username: str):
    statement = select(models.Users).where(models.Users.username == username).where(models.Users.is_admin == True).where(models.Users.is_disabled == False)
    results = db.exec(statement)
    return results.first()

def secu_get_user_by_email(db: Session, email: str):
    statement = select(models.Users).where(models.Users.email == email).where(models.Users.is_admin == True).where(models.Users.is_disabled == False)
    results = db.exec(statement)
    return results.first()

def loadsecurity(db: Session, json):
    # Gestion du password vide
    if json['password']=="":
        print(f"{colors.BColors.RED}ERROR{colors.BColors.END}:    Security load error, password null")
        return {"fonction": "loadsecurity", "erreur": 'Le mot de passe ne peut pas être vide'}
    try:
        user = get_user_by_username(db, json['username'])     
        user_dict = models.Users(
            username = json['username'],
            full_name = json['full_name'],
            email = json.get('email', json['username'] + '@admin.local'),
            hashed_password = hash_password(json['password']),
            is_admin = True,
            is_disabled = False,
            is_visible = False
        )
        if not user:
            db.add(user_dict)
            db.commit()
            db.refresh(user_dict)
            print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     Utilisateur de sécurité créé")
            return {"result": 'Utilisateur de sécurité créé'}
        else:
            statement = select(models.Users).where(models.Users.username == user_dict.username)
            result = db.exec(statement).one()
            result.username = user_dict.username
            result.full_name = user_dict.full_name
            result.email = user_dict.email
            result.hashed_password = user_dict.hashed_password
            result.is_admin = True
            result.is_disabled = False
            result.is_visible = False
            db.add(result)
            db.commit()
            db.refresh(result)
            
            print(f"{colors.BColors.GREEN}INFO{colors.BColors.END}:     Utilisateur de sécurité modifié")
            return {"result": 'Utilisateur de sécurité modifié'}
    except:
        print(f"{colors.BColors.RED}ERROR{colors.BColors.END}:    Erreur lors du chargement de la sécurité")
        return {"fonction": "loadsecurity", "erreur": 'Erreur lors du chargement de la sécurité'}

    
############### Users #############

def get_user_by_username(db: Session, username: str):
    statement = select(models.Users).where(models.Users.username == username)
    results = db.exec(statement)
    return results.first()

def get_user_by_email(db: Session, email: str):
    statement = select(models.Users).where(models.Users.email == email)
    results = db.exec(statement)
    return results.first()

def get_user_by_id(db: Session, user_id: int):
    statement = select(models.Users).where(models.Users.id == user_id)
    results = db.exec(statement)
    return results.first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    statement = select(models.Users).where(models.Users.is_disabled == False).where(models.Users.is_visible == True).offset(skip).limit(limit)
    results = db.exec(statement)
    return results.all()

def build_user_read(user: models.Users):
    return schemas.UserRead(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        image_url=user.image_url,
        arrival=user.arrival,
        is_disabled=user.is_disabled,
        is_admin=user.is_admin,
        is_visible=user.is_visible,
        created_at=user.created_at
    )

def create_user(db: Session, user):
    db_user = models.Users(
        username=user.username,
        full_name=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        is_admin=False,
        is_disabled=False,
        is_visible=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return build_user_read(db_user)

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    if user_update.username is not None:
        user.username = user_update.username
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.password is not None:
        user.hashed_password = hash_password(user_update.password)
    if user_update.is_disabled is not None:
        user.is_disabled = user_update.is_disabled
    if user_update.is_admin is not None:
        user.is_admin = user_update.is_admin
    if user_update.is_visible is not None:
        user.is_visible = user_update.is_visible
    db.add(user)
    db.commit()
    db.refresh(user)
    return build_user_read(user)

def delete_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if not user:
        return {"fonction": "delete_user", "erreur": "L'utilisateur n'existe pas"}
    db.delete(user)
    db.commit()
    return {"fonction": "delete_user", "resultat": "Utilisateur supprimé"}