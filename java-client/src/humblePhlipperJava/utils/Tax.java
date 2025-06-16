package humblePhlipperJava.utils;

public class Tax {
    /**
     * Returns the post-GE-tax price of an item.
     * @param ID the item ID
     * @param price the price of the item
     * @return the post-tax price of the item
     */

    public static int getPostTaxPrice(int ID, int price) {
        if (OsrsConstants.TAX_EXEMPT_DS.contains(ID)) { return price;}
        return (int) Math.max(Math.ceil((1- OsrsConstants.GE_TAX_RATE) * price), price - OsrsConstants.MAX_GE_TAX);
    }

    public static double getPostTaxPrice(int ID, double price) {
        if (OsrsConstants.TAX_EXEMPT_DS.contains(ID)) { return price;}
        return Math.max(Math.ceil((1- OsrsConstants.GE_TAX_RATE) * price), price - OsrsConstants.MAX_GE_TAX);
    }
}
