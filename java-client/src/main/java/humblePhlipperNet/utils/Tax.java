package humblePhlipperNet.utils;

public class Tax {
    /**
     * Returns the post-GE-tax price of an item.
     * @param ID the item ID
     * @param price the price of the item
     * @return the post-tax price of the item
     */

    public static int getPostTaxPrice(int ID, int price) {
        if (OsrsConstants.TAX_EXEMPT_IDS.contains(ID)) { return price;}
        return Math.max(price - (int) Math.floor(OsrsConstants.GE_TAX_RATE * price), price - OsrsConstants.MAX_GE_TAX);

    }
}
