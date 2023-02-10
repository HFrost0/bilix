from datetime import datetime, timedelta
from .app import app
from .user import User
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password):
    return pwd_context.hash(password)


def verify_password(password, hashed_password):
    return pwd_context.verify(password, hashed_password)


# only for test by now....
fake_users_db = {
    "huang": User(username="huang", password=hash_password("nishishabi")),
    "sb": User(username="sb", password=hash_password("sbsbsb"))
}


def decode_token(token: str) -> User:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload['sub']
    user = fake_users_db[username]
    return user


def encode_token(user: User) -> str:
    data = {'sub': user.username, 'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        user = decode_token(token)
    except (KeyError, JWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username")
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    token = encode_token(user)
    return {"access_token": token, "token_type": "bearer"}


@app.on_event("shutdown")
async def clean_user():
    for user in fake_users_db.values():
        for d in user.downloaders.values():
            await d.aclose()
        for s in user.active_sockets:
            await s.close()
