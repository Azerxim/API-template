from typing import List, Annotated
from fastapi import Depends
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from . import crud, schemas
from .database import get_db

# Créer un routeur pour les routes utilisateur
router = APIRouter(prefix="/api/users", tags=["Users"])

# -----------------------------------------------
@router.post("/create/", response_model=schemas.UserRead)
def create_user(current_user: Annotated[schemas.Users, Depends(crud.secu_get_current_active_user)], user: schemas.UserLogin, db: Session = Depends(get_db)):
    """Créer un nouvel utilisateur"""
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Le nom d'utilisateur ou l'email est incorrect")
    
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Le nom d'utilisateur ou l'email est incorrect")
    return crud.create_user(db=db, user=user)

# -----------------------------------------------
@router.put("/update/{id}/", response_model=schemas.UserRead)
def update_user(current_user: Annotated[schemas.Users, Depends(crud.secu_get_current_active_user)], id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un utilisateur existant"""
    db_user = crud.get_user_by_id(db, user_id=id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return crud.update_user(db=db, user_id=id, user_update=user)

# -----------------------------------------------
@router.delete("/delete/{id}/")
def delete_user(current_user: Annotated[schemas.Users, Depends(crud.secu_get_current_active_user)], id: int, db: Session = Depends(get_db)):
    """Supprimer un utilisateur"""
    db_user = crud.get_user_by_id(db, user_id=id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return crud.delete_user(db=db, user_id=id)

# -----------------------------------------------
@router.get("/name/{username}/", response_model=schemas.UserRead)
def read_user_by_username(username: str, db: Session = Depends(get_db)):
    """Récupérer un utilisateur par nom d'utilisateur"""
    db_user = crud.get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return crud.build_user_read(db_user)

# -----------------------------------------------
@router.get("/id/{user_id}/", response_model=schemas.UserRead)
def read_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """Récupérer un utilisateur par ID"""
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return crud.build_user_read(db_user)

# -----------------------------------------------
@router.get("/list/", response_model=List[schemas.UserRead])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer la liste des utilisateurs"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return [crud.build_user_read(user) for user in users]
