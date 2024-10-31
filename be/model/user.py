import logging
import sqlite3 as sqlite
import time
import jwt

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from be.model import db_conn
from be.model import error


# encode a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }


def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    return encoded.encode("utf-8").decode("utf-8")

# decode a JWT to a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }
def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded


class User(db_conn.DBConn):
    token_lifetime: int = 3600  # 3600 second

    def __init__(self):
        db_conn.DBConn.__init__(self)

    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:
            logging.error(str(e))
            return False

    def register(self, user_id: str, password: str):
        try:
            # 插入前进行重复冲突检查
            existing_user = self.conn.user_col.find_one({"user_id": user_id})

            if existing_user:
                return 530, "User already exists"

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)

            # 确定无冲突后执行插入
            self.conn.user_col.insert_one({
                "user_id": user_id,
                "password": password,
                "balance": 0,
                "token": token,
                "terminal": terminal
            })
        except Exception as e:
            return 530, str(e)
        return 200, "ok"

    def check_token(self, user_id: str, token: str) -> (int, str):
        user_doc = self.conn.user_col.find_one({"user_id": user_id}, {"token": 1})

        if user_doc is None:
            return error.error_authorization_fail()

        db_token = user_doc.get("token")

        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()

        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> (int, str):
        user_doc = self.conn.user_col.find_one({"user_id": user_id})

        if user_doc is None:
            return error.error_authorization_fail()

        if password != user_doc.get("password"):
            return error.error_authorization_fail()

        return 200, "ok"

    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        token = ""
        try:
            # 用户密码检查
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)
            result = self.conn.user_col.update_one(
                {"user_id": user_id},
                {"$set": {"token": token, "terminal": terminal}}
            )
            if result.modified_count == 0:
                return 401, "Authorization failed", ""
        except Exception as e:
            return 500, str(e), ""
        return 200, "OK", token

    def logout(self, user_id: str, token: str) -> (int, str):
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)

            result = self.conn.user_col.find_one_and_update(
                {"user_id": user_id},
                {"$set": {"token": dummy_token, "terminal": terminal}},
                return_document=ReturnDocument.AFTER
            )
            if result is None:
                return error.error_authorization_fail()

        except Exception as e:
            return 530, str(e)

        return 200, "ok"

    def unregister(self, user_id: str, password: str) -> (int, str):
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message

            result = self.conn.user_col.delete_one({"user_id": user_id})

            if result.deleted_count == 1:
                return 200, "ok"
            else:
                return error.error_authorization_fail()

        except Exception as e:
            return 530, str(e)

    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> (int, str):
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)

            result = self.conn.user_col.update_one(
                {"user_id": user_id},
                {"$set": {"password": new_password, "token": token, "terminal": terminal}}
            )

            if result.modified_count == 0:
                return error.error_authorization_fail()

            return 200, "ok"
        except Exception as e:
            return 530, str(e)
