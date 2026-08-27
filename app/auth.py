import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = "sqlite:///./data/users.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


# ============================================================
# USER MODEL
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    email = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash = Column(
        String,
        nullable=False,
    )


Base.metadata.create_all(
    bind=engine
)


# ============================================================
# PASSWORD HASHING
# ============================================================
password_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)

def hash_password(password):
    return password_context.hash(
        password
    )


def verify_password(
    plain_password,
    hashed_password,
):
    return password_context.verify(
        plain_password,
        hashed_password,
    )


# ============================================================
# JWT AUTHENTICATION
# ============================================================

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "change-this-secret-before-deploying",
)

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(user_id):

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token):

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[
                JWT_ALGORITHM
            ],
        )

        user_id = payload.get("sub")

        if user_id is None:
            return None

        return int(user_id)

    except JWTError:
        return None