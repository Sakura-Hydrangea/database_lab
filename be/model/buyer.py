import sqlite3 as sqlite
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
import pymongo.errors
import time


class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    # 下单操作
    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            # 检查用户和店铺是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)

            # 生成唯一订单ID
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
            total_price = 0

            for book_id, count in id_and_count:
                # 查询库存和价格信息
                row = self.conn.store_col.find_one(
                    {"book_id": book_id, "store_id": store_id},
                    {"book_id": 1, "stock_level": 1, "book_price": 1}
                )

                if row is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)

                stock_level = row["stock_level"]
                price = row["book_price"]

                # 检查库存
                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                # 更新库存
                result = self.conn.store_col.update_one(
                    {"store_id": store_id, "book_id": book_id, "stock_level": {"$gte": count}},
                    {"$inc": {"stock_level": -count}}
                )

                if result.modified_count == 0:
                    return error.error_stock_level_low(book_id) + (order_id,)

                # 插入订单详情
                self.conn.new_order_detail_col.insert_one(
                    {"order_id": uid, "book_id": book_id, "count": count, "price": price}
                )
                total_price += price * count

            # 设置订单支付截止时间
            current_time = int(time.time())
            payment_ddl = current_time + 15
            # 插入订单基础信息
            self.conn.new_order_col.insert_one({
                "order_id": uid, "store_id": store_id, "user_id": user_id,
                "payment_status": "no_pay", "payment_ddl": payment_ddl,
                "total_price": total_price
            })
            order_id = uid

        except BaseException as e:
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    # 付款操作
    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            # 获取订单信息
            order = self.conn.new_order_col.find_one({"order_id": order_id})
            if order is None:
                return error.error_invalid_order_id(order_id)
            if order["payment_status"] != "no_pay":
                return error.error_invalid_payment_status(order_id)

            # 验证买家身份和密码
            user = self.conn.user_col.find_one({"user_id": user_id}, {"balance": 1, "password": 1})
            if user is None:
                return error.error_non_exist_user_id(user_id)
            if user["password"] != password:
                return error.error_authorization_fail()

            # 检查余额是否足够
            total_price = order["total_price"]
            if user["balance"] < total_price:
                return error.error_not_sufficient_funds(order_id)

            # 扣除买家余额并增加卖家余额
            self.conn.user_col.update_one({"user_id": user_id}, {"$inc": {"balance": -total_price}})
            self.conn.user_col.update_one({"user_id": order["store_id"]}, {"$inc": {"balance": total_price}})

            # 更新订单状态为已支付
            self.conn.new_order_col.update_one({"order_id": order_id}, {"$set": {"payment_status": "paid"}})

        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 增加资金
    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            # 验证用户身份和密码
            user = self.conn.user_col.find_one({"user_id": user_id}, {"password": 1})
            if user is None or user.get("password") != password:
                return error.error_authorization_fail()

            # 增加用户余额
            self.conn.user_col.update_one({"user_id": user_id}, {"$inc": {"balance": add_value}})

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 图书查找
    def book_search(self, store_id=None, book_id=None, book_title=None, book_tags=None, book_author=None):
        try:
            query_conditions = {}
            if store_id:
                query_conditions["store_id"] = store_id
            if book_id:
                query_conditions["book_id"] = book_id
            if book_title:
                query_conditions["book_title"] = {"$regex": book_title, "$options": "i"}
            if book_tags:
                query_conditions["book_tags"] = {"$all": book_tags}
            if book_author:
                query_conditions["book_author"] = book_author

            result = list(self.conn.store_col.find(query_conditions, {}).limit(10))
            if not result:
                return error.error_non_exist_book_id(book_id)

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 删除订单
    def delete_order(self, user_id, order_id) -> (int, str):
        try:
            # 获取订单信息
            order = self.conn.new_order_col.find_one({"order_id": order_id})
            if not order:
                return error.error_non_order_delete(user_id)

            # 根据订单支付状态进行处理
            if order["payment_status"] == "paid":
                total_price = order["total_price"]
                # 返还买家余额
                self.conn.user_col.update_one({"user_id": user_id}, {"$inc": {"balance": total_price}})
                # 扣减卖家余额
                self.conn.user_col.update_one({"user_id": order["store_id"]}, {"$inc": {"balance": -total_price}})

            # 删除订单及详情
            self.conn.new_order_col.delete_one({"order_id": order_id})
            self.conn.new_order_detail_col.delete_many({"order_id": order_id})

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 订单查询
    def search_order(self, user_id) -> (int, str):
        try:
            # 删除超时未支付订单
            current_time = int(time.time())
            expired_orders = self.conn.new_order_col.find(
                {"user_id": user_id, "payment_ddl": {"$lt": current_time}, "payment_status": "no_pay"}
            )
            expired_order_ids = [order["order_id"] for order in expired_orders]
            self.conn.new_order_col.delete_many({"order_id": {"$in": expired_order_ids}})
            self.conn.new_order_detail_col.delete_many({"order_id": {"$in": expired_order_ids}})

            # 返回用户所有订单
            orders = list(self.conn.new_order_col.find({"user_id": user_id}))
            if not orders:
                return error.empty_order_search(user_id)

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 接收订单
    def receive(self, user_id: str, store_id: str, order_id: str) -> (int, str):
        try:
            # 获取订单信息
            order = self.conn.new_order_col.find_one({"order_id": order_id})
            if not order or order["user_id"] != user_id:
                return error.error_non_exist_user_id(user_id)
            if order["store_id"] != store_id:
                return error.error_non_exist_store_id(store_id)
            if order["payment_status"] == "no_pay":
                return 521, "订单未付款"
            if order["payment_status"] == "received":
                return 523, "订单已接收"

            # 更新订单状态为已接收
            self.conn.new_order_col.update_one({"order_id": order_id}, {"$set": {"payment_status": "received"}})

        except BaseException as e:
            return 532, "{}".format(str(e))

        return 200, "ok"


