package humblePhlipperNet.utils;

public class Tax {
    public static int getPostTaxPrice(int price, int ID) {
        if (OsrsConstants.TAX_EXEMPT_IDS.contains(ID)) { return price;}
        return Math.max(price - (int) Math.floor(OsrsConstants.GE_TAX_RATE * price), price - OsrsConstants.MAX_GE_TAX);

    }
}
