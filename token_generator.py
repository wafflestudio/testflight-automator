import datetime
import jwt
import requests

keyId = "K3TNC9JCDQ"
issuer = "719d926e-ca2d-425d-a926-02d603c8a11f"


def _read_secret_key() -> str:
    with open(f"AuthKey_{keyId}.p8", "r") as f:
        return f.read()


def get_jwt_token():
    alg = "ES256"
    time_now = datetime.datetime.now()
    time_expired = time_now + datetime.timedelta(minutes=10)

    headers = {"alg": alg, "kid": keyId, "typ": "JWT"}

    payload = {
        "iss": issuer,
        "iat": int(time_now.strftime("%s")),
        "exp": int(time_expired.strftime("%s")),
        "aud": "appstoreconnect-v1",
    }

    secret = _read_secret_key()
    token = jwt.encode(payload, secret, algorithm=alg, headers=headers)
    return token


if __name__ == "__main__":
    token = get_jwt_token()
    print(token)
