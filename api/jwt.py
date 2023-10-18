import os
import sys
import json
import datetime
import uuid  # Import the 'uuid' module for generating UUIDs


def expiration_in(minutes):
    creation = datetime.datetime.now(tz=datetime.timezone.utc)
    expiration = creation + datetime.timedelta(minutes=minutes)
    return creation, expiration


def generate_claims(username, roles):
    _, exp = expiration_in(20)
    jti = f"{int(datetime.datetime.utcnow().timestamp())}_{str(uuid.uuid4())}"

    print(username, roles)

    claims = {
        "aud": "krakend.local.gd",
        "iss": "auth.local.gd",
        "sub": username,
        "jti": jti,
        "roles": roles,
        "exp": int(exp.timestamp()),
    }
    token = {
        "access_token": claims,
        "refresh_token": claims,
        "exp": int(exp.timestamp()),
    }

    return token