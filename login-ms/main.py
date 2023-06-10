import uvicorn
import jwt
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


### Database setup code:
SQLALCHEMY_DATABASE_URL = 'sqlite:///users.db'
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
db = SessionLocal()

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True)
    password_hash = Column(String(128))

Base.metadata.create_all(bind=engine)
#########################


### JWT authentication:
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
    token = credentials.credentials
    user = authenticate_token(token)
    if not user:
        raise HTTPException(status_code=401, detail='Invalid token')
    return user


def authenticate_token(token: str) -> User:
    try:
        payload = jwt.decode(token, 'supersecretkey', algorithms=['HS256'])
        user_id = payload.get('identity')
        user = db.query(User).get(user_id)
        return user
    except:
        return None
#########################


class UserAuthenticate(BaseModel):
    username: str
    password: str


class Controller():
    def __init__(self) -> None:
        self.router = APIRouter()
        self.router.add_api_route("/register", self.register, methods=["POST"])
        self.router.add_api_route("/login", self.login, methods=["POST"])
        self.router.add_api_route("/protected", self.protected, methods=["GET"])
    def register(self, user: UserAuthenticate):
            existing_user = db.query(User).filter_by(username=user.username).first()
            if existing_user:
                raise HTTPException(status_code=400, detail='Username already exists')

            password_hash = pwd_context.hash(user.password)
            new_user = User(username=user.username, password_hash=password_hash)
            db.add(new_user)
            db.commit()
            return {'message': 'User registered successfully'}
    def login(self, user: UserAuthenticate):
        db_user = db.query(User).filter_by(username=user.username).first()
        if not db_user or not pwd_context.verify(user.password, db_user.password_hash):
            raise HTTPException(status_code=401, detail='Invalid credentials')
        token = jwt.encode({'identity': db_user.id}, 'supersecretkey', algorithm='HS256')
        return {'access_token': token}

    def protected(self, user: User = Depends(get_current_user)):
        return {'message': f'Logged in as {user.username}'}


if __name__ == "__main__":
    app = FastAPI()
    cntrllr = Controller()
    app.include_router(cntrllr.router)
    localhost = "0.0.0.0"
    port = 80
    uvicorn.run(app, host=localhost, port=port)
