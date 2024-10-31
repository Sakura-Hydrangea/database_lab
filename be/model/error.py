error_code = {
    401: "authorization fail.",
    511: "non exist user id {}",
    512: "exist user id {}",
    513: "non exist store id {}",
    514: "exist store id {}",
    515: "non exist book id {}",
    516: "exist book id {}",
    517: "stock level low, book id {}",
    518: "invalid order id {}",
    519: "not sufficient funds, order id {}",
    520: "non order to delete, user id {}",
    521: "repay error, order id {}",
    522: "non order to set payment status, order id {}",
    523: "non exist order, order id {}",
    524: "unable to delete order, order id {}",
    525: "empty order search, user id {}",
    526: "unknown error occurred, order id {}",
    527: "database operation failed, error: {}",
    528: "MongoDB operation error: {}",
}


def error_non_exist_user_id(user_id):
    return 511, error_code[511].format(user_id)


def error_exist_user_id(user_id):
    return 512, error_code[512].format(user_id)


def error_non_exist_store_id(store_id):
    return 513, error_code[513].format(store_id)


def error_exist_store_id(store_id):
    return 514, error_code[514].format(store_id)


def error_non_exist_book_id(book_id):
    return 515, error_code[515].format(book_id)


def error_exist_book_id(book_id):
    return 516, error_code[516].format(book_id)


def error_stock_level_low(book_id):
    return 517, error_code[517].format(book_id)


def error_invalid_order_id(order_id):
    return 518, error_code[518].format(order_id)


def error_not_sufficient_funds(order_id):
    return 519, error_code[519].format(order_id)


def error_non_order_delete(user_id):
    return 520, error_code[520].format(user_id)


def error_order_repay(order_id):
    return 521, error_code[521].format(order_id)


def error_non_order_pay(order_id):
    return 522, error_code[522].format(order_id)


def error_non_exist_order(order_id):
    return 523, error_code[523].format(order_id)


def error_unable_to_delete(order_id):
    return 524, error_code[524].format(order_id)


def empty_order_search(user_id):
    return 525, error_code[525].format(user_id)


def error_authorization_fail():
    return 401, error_code[401]


def error_and_message(code, message):
    return code, message


def error_invalid_payment_status(order_id):
    return 528, error_code[528].format(order_id)


def error_database_failure(error_message):
    return 527, error_code[527].format(error_message)
