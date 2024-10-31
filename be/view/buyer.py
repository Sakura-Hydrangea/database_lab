from flask import Blueprint
from flask import request
from flask import jsonify
from be.model.buyer import Buyer

bp_buyer = Blueprint("buyer", __name__, url_prefix="/buyer")


@bp_buyer.route("/new_order", methods=["POST"])
def new_order():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    books: [] = request.json.get("books")
    id_and_count = []
    for book in books:
        book_id = book.get("id")
        count = book.get("count")
        id_and_count.append((book_id, count))

    b = Buyer()
    code, message, order_id = b.new_order(user_id, store_id, id_and_count)
    return jsonify({"message": message, "order_id": order_id}), code


@bp_buyer.route("/payment", methods=["POST"])
def payment():
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    password: str = request.json.get("password")
    b = Buyer()
    code, message = b.payment(user_id, password, order_id)
    return jsonify({"message": message}), code


@bp_buyer.route("/add_funds", methods=["POST"])
def add_funds():
    user_id = request.json.get("user_id")
    password = request.json.get("password")
    add_value = request.json.get("add_value")
    b = Buyer()
    code, message = b.add_funds(user_id, password, add_value)
    return jsonify({"message": message}), code


@bp_buyer.route("/search_book", methods=["POST"])
def book_search():
    store_id: str = request.json.get("store_id")
    book_id = request.json.get("book_id")
    book_title = request.json.get("book_title")
    book_tags = request.json.get("book_tags")
    book_author = request.json.get("book_author")
    b = Buyer()
    code, message = b.book_search(
        store_id, book_id, book_title, book_tags, book_author
    )
    return jsonify({"message": message}), code


# 接受删除订单请求并调用后端逻辑实现
@bp_buyer.route("/delete_order", methods=["POST"])
def delete_order():
    # 请求需传入user_id
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    b = Buyer()
    code, message = b.delete_order(user_id, order_id)
    return jsonify({"message": message}), code


# 接收搜索订单请求
@bp_buyer.route("/search_order", methods=["POST"])
def search_order():
    # 请求需传入user_id
    user_id: str = request.json.get("user_id")
    b = Buyer()
    code, message = b.search_order(user_id)
    return jsonify({"message": message}), code


@bp_buyer.route("/receive", methods=["POST"])
def receive():
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    store_id: str = request.json.get("store_id")
    b = Buyer()
    code, message = b.receive(user_id, store_id, order_id)
    return jsonify({"message": message}), code
