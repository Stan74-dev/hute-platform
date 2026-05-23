from decimal import Decimal, ROUND_HALF_UP


TWOPLACES = Decimal("0.01")


def q(value):
    return Decimal(str(value or 0)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def calculate_tax_from_product(unit_price, quantity, tax_rate):
    unit_price = q(unit_price)
    quantity = Decimal(str(quantity or 0))

    line_base = q(unit_price * quantity)

    if tax_rate is None:
        return {
            "rate_percent": q(0),
            "line_subtotal": line_base,
            "tax_amount": q(0),
            "line_total": line_base,
        }

    rate_percent = q(tax_rate.rate_percent)
    rate_fraction = rate_percent / Decimal("100")

    if tax_rate.category in ["zero_rated", "exempt"]:
        return {
            "rate_percent": rate_percent,
            "line_subtotal": line_base,
            "tax_amount": q(0),
            "line_total": line_base,
        }

    if tax_rate.tax_type == "inclusive":
        divisor = Decimal("1.00") + rate_fraction
        subtotal = q(line_base / divisor)
        tax_amount = q(line_base - subtotal)
        total = line_base
    else:
        subtotal = line_base
        tax_amount = q(subtotal * rate_fraction)
        total = q(subtotal + tax_amount)

    return {
        "rate_percent": rate_percent,
        "line_subtotal": subtotal,
        "tax_amount": tax_amount,
        "line_total": total,
    }