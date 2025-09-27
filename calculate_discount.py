# calculate_discount.py

def calculate_discount(price, discount_percent):
    """
    Return the final price after applying the discount if it's >= 20%.
    Otherwise, return the original price unchanged.
    """
    if discount_percent >= 20:
        return price * (1 - discount_percent / 100)
    return price


if __name__ == "__main__":
    try:
        price = float(input("Enter the original price: "))
        discount_percent = float(input("Enter the discount percentage: "))
        if price < 0 or discount_percent < 0:
            raise ValueError("Price and discount must be non-negative.")
    except ValueError as e:
        print(f"Invalid input: {e}")
    else:
        final_price = calculate_discount(price, discount_percent)
        if final_price != price:
            print(f"Final price after {discount_percent:.0f}% discount: {final_price:.2f}")
        else:
            print(f"No discount applied. Final price: {final_price:.2f}")
