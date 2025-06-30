import osrs_constants

def get_post_tax_price(item_id: int, price: int) -> int:
    """
    Compute the post-tax price for an item.

    Parameters
    ----------
    item_id : int
        If the item is tax-exempt, returns the original price.
    price : int
        Pre-tax sell price of the item.
        
    Returns
    -------
    int
        Post-tax price after applying the Grand Exchange tax.
    """
    if item_id in osrs_constants.TAX_EXEMPT_IDS:
        return price
    return max(price - int(osrs_constants.GE_TAX_RATE * price), price - osrs_constants.MAX_GE_TAX)