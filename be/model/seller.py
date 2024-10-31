from be.model import error
from be.model import db_conn
import pymongo
import time


class Seller(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def add_book(self, user_id: str, store_id: str, book_id: str, book_title: str, book_tags, book_author,
                 book_price: str,
                 stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            data = {
                "store_id": store_id,
                "book_id": book_id,
                "book_title": book_title,
                "book_tags": book_tags,
                "book_author": book_author,
                "book_price": book_price,
                "stock_level": stock_level
            }
            # 插入数据到MongoDB
            self.conn.store_col.insert_one(data)

        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"  # 成功添加书籍，返回状态码200和消息

    def add_stock_level(
            self, user_id: str, store_id: str, book_id: str, add_stock_level: int
    ):
        try:

            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            # self.conn.execute(
            #     "UPDATE store SET stock_level = stock_level + ? "
            #     "WHERE store_id = ? AND book_id = ?",
            #     (add_stock_level, store_id, book_id),
            # )

            filter_query = {"store_id": store_id, "book_id": book_id}
            update_query = {"$inc": {"stock_level": add_stock_level}}

            self.conn.store_col.update_one(filter_query, update_query)
        except BaseException as e:
            return 500, "{}".format(str(e))

        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)

            data = {
                "store_id": store_id,
                "user_id": user_id
            }

            self.conn.user_store_col.insert_one(data)

        except BaseException as e:
            return 500, "{}".format(str(e))
        return 200, "ok"

    def search_order(self, user_id) -> (int, str):
        try:
            # 搜索前遍历订单删除超时订单
            current_time = int(time.time())
            payment_overtime_order_ids = [order['order_id'] for order in
                                          self.conn.new_order_col.find({"payment_ddl": {"$lt": current_time},
                                                                        "payment_status": "no_pay"},
                                                                       {"order_id": 1})]
            self.conn.new_order_col.delete_many({"order_id": {"$in": payment_overtime_order_ids}})
            self.conn.new_order_detail_col.delete_many({"order_id": {"$in": payment_overtime_order_ids}})

            # 将用户作为卖家进行搜索
            # 获取卖家名下店铺
            seller_store_ids = [store['store_id'] for store in
                                self.conn.user_store_col.find({"user_id": user_id}, {"store_id": 1})]
            # 通过店铺store_id搜索订单order_id
            seller_order_ids = [order['order_id'] for order in
                                self.conn.new_order_col.find({"store_id": {"$in": seller_store_ids}},
                                                             {"order_id": 1})]
            if not seller_order_ids:
                return error.empty_order_search(user_id)
            self.conn.new_order_col.find({"order_id": {"$in": seller_order_ids}}, {})

        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def deliver(self, user_id: str, store_id: str, order_id: str) -> (int, str):
        try:
            result = self.conn.new_order_col.find_one({"order_id": order_id})
            if result is None:
                return error.error_non_exist_order(order_id)

            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)

            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)

            result = self.conn.new_order_col.find_one({"order_id": order_id})
            status = result['payment_status']

            if status == "no_pay":
                return 521, {"no_pay"}
            elif status == "shipped" or status == "received":
                return 522, {"shipped"}

            self.conn.new_order_col.update_one({"order_id": order_id}, {"$set": {"payment_status": 'shipped'}})  # 已发货

        except BaseException as e:
            return 531, "{}".format(str(e))
        return 200, "ok"
