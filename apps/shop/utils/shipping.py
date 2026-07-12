def calculate_post_price(weight):
    if weight < 300:
        return 45000
    elif 300 <= weight < 500:
        return 65000
    else:
        return 95000
