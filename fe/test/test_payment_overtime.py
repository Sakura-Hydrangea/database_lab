import pytest

from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book

import uuid
import time


class TestPaymentOvertime:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 卖家信息初始化
        self.seller_id = "test_search_order_seller_{}".format(str(uuid.uuid1()))
        self.seller_password = self.seller_id
        self.store_id = "test_search_order_store_store_{}".format(str(uuid.uuid1()))

        # 买家信息初始化与创建
        self.buyer_id = "test_search_order_buyer_id_{}".format(str(uuid.uuid1()))
        self.buyer_password = self.buyer_id
        self.buyer = register_new_buyer(self.buyer_id, self.buyer_password)

        # 创建卖家店铺并读入书籍
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, self.buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        self.buy_book_info_list = gen_book.buy_book_info_list
        assert ok

        self.seller = gen_book.seller
        yield

    def test_delete_payment_overtime(self):
        code, self.order_id = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200

        # 搜索时执行删除超时订单
        code = self.buyer.search_order()
        assert code == 200

        # 等待20秒
        time.sleep(20)

        # 搜索时执行删除超时订单
        code = self.buyer.search_order()
        assert code == 525

    # 完成付款则订单未删除
    def test_payment_completely(self):
        code, self.order_id = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200

        self.total_price = 0
        for item in self.buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            else:
                self.total_price = self.total_price + book.price * num

        code = self.buyer.add_funds(self.total_price)
        assert code == 200

        # 刚下单成功订单存在
        code = self.buyer.search_order()
        assert code == 200

        # 完成付款
        code = self.buyer.payment(self.order_id)
        assert code == 200

        # 等待20秒
        time.sleep(20)

        # 已付款订单未删除,仍存在
        code = self.buyer.search_order()
        assert code == 200
