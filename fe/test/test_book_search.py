import pytest

from fe.access.new_seller import register_new_seller
from fe.access.new_buyer import register_new_buyer
from fe.access import book
import uuid


class TestBookSearch:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # do before test
        self.seller_id = "test_book_search_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_book_search_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_book_search_buyer_id_{}".format(str(uuid.uuid1()))

        # 初始化搜索书籍相关信息
        self.book_id = None
        self.book_title = None
        self.book_tags = None
        self.book_author = None
        self.search_store_id = None

        self.password = self.seller_id
        self.seller = register_new_seller(self.seller_id, self.password)
        self.buyer = register_new_buyer(self.buyer_id, self.password)

        code = self.seller.create_store(self.store_id)
        assert code == 200

        book_db = book.BookDB()
        self.books = book_db.get_book_info(0, 5)
        for b in self.books:
            code = self.seller.add_book(self.store_id, 0, b)
            assert code == 200

        yield
        # do after test

    def test_book_id(self):
        for bk in self.books:
            self.book_id = bk.__dict__.get("id")
            code = self.buyer.book_search(self.search_store_id, self.book_id, self.book_title, self.book_tags,
                                          self.book_author)
            assert code == 200

    def test_book_title(self):
        for bk in self.books:
            self.book_title = bk.__dict__.get("title")
            code = self.buyer.book_search(self.search_store_id, self.book_id, self.book_title, self.book_tags,
                                          self.book_author)
            assert code == 200

    def test_book_tags(self):
        for bk in self.books:
            self.book_tags = bk.__dict__.get("tags")
            code = self.buyer.book_search(self.search_store_id, self.book_id, self.book_title, self.book_tags,
                                          self.book_author)
            assert code == 200

    def test_book_author(self):
        for bk in self.books:
            self.book_author = bk.__dict__.get("author")
            code = self.buyer.book_search(self.search_store_id, self.book_id, self.book_title, self.book_tags,
                                          self.book_author)
            assert code == 200

    def test_book_in_store(self):
        for bk in self.books:
            self.search_store_id = self.store_id
            self.book_id = bk.__dict__.get("id")
            code = self.buyer.book_search(self.search_store_id, self.book_id, self.book_title, self.book_tags,
                                          self.book_author)
            assert code == 200

    def test_book_not_exist(self):
        for bk in self.books:
            self.book_id = bk.__dict__.get("id") + "000"
            code = self.buyer.book_search(self.search_store_id, self.book_id, self.book_title, self.book_tags,
                                          self.book_author)
            assert code != 200




