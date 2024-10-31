import pytest

from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
import uuid


class TestSearchOrder:
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
        self.seller = gen_book.seller
        assert ok

        yield

    # 创建订单并搜索
    def test_ok(self):
        code, self.order_id = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200

        code = self.buyer.search_order()
        assert code == 200

        code = self.seller.search_order()
        assert code == 200

    # 测试搜索结果为空
    def test_empty_order_search(self):
        # 不创建订单直接进行搜索
        code = self.seller.search_order()
        assert code == 525

        code = self.buyer.search_order()
        assert code == 525
