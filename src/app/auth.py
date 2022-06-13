from typing import Optional, TypedDict

from flask import request

from .errors.exceptions import AppError


class Token(TypedDict):
    uid: int


class User(TypedDict):
    id: int


class InvalidAccessTokenError(Exception):
    pass


def decode_token(token: Optional[str]) -> Token:
    """Simulating JWT token decoding - given token will be equal to user_id."""
    if not token:
        raise InvalidAccessTokenError
    return {"uid": int(token)}


def current_user() -> User:
    try:
        token = decode_token(request.headers.get("authorization"))
        user = User(id=token["uid"])
        return user
    except InvalidAccessTokenError as exc:
        raise AppError(error_code="INVALID_ACCESS_TOKEN", status_code=401) from exc
