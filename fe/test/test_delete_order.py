import pytest

import uuid

from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access import buyer


class TestDeleteOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 卖家信息初始化
        self.seller_id = "test_delete_order_seller_{}".format(str(uuid.uuid1()))
        self.seller_password = self.seller_id
        self.store_id = "test_delete_order_store_{}".format(str(uuid.uuid1()))

        # 买家信息初始化与创建
        self.buyer_id = "test_delete_order_buyer_id_{}".format(str(uuid.uuid1()))
        self.buyer_password = self.buyer_id
        self.buyer = register_new_buyer(self.buyer_id, self.buyer_password)

        yield

    # 测试完整删除订单且ok的流程
    def test_delete_ok(self):
        # 创建卖家店铺并读入书籍
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        self.buy_book_info_list = gen_book.buy_book_info_list
        assert ok

        code, self.order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200

        # 删除buyer
        code = self.buyer.delete_order(self.buyer_id, self.order_id)
        assert code == 200

    # 测试无订单时返回错误代码520
    def test_non_order_delete(self):
        # 删除buyer
        code = self.buyer.delete_order(self.buyer_id, "test_delete_order_buyer_id")
        assert code == 520  # error code of non_order_delete
