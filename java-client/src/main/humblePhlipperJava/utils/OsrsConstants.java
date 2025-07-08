package humblePhlipperJava.utils;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

public class OsrsConstants {
    public static final int NUM_INV_SLOTS = 28;
    public static final int NUM_GE_SLOTS = 8;
    public static final int COINS_ID = 995;
    public static final int BOND_ID = 13190;
    public static final Set<Integer> TRADE_RESTRICTED_IDS = new HashSet<>(Arrays.asList(1521, 1519, 1515, 317, 315, 321, 319, 377, 379, 434, 1761, 436, 438, 440, 442, 444, 453, 447, 449, 451, 1739, 229, 227, 1937, 313, 314, 221, 245, 556, 555, 557, 554, 558, 562));
    public static final Set<Integer> TAX_EXEMPT_IDS = new HashSet<>(Arrays.asList(13190, 1755, 5325, 1785, 2347, 1733, 233, 5341, 8794, 5329, 5343, 1735, 952, 5331));
    public static final float GE_TAX_RATE = 0.02F;
    public static final int GE_TAX_PERCENTAGE = 2;
    public static final int MAX_GE_TAX = 5000000;
    public static final int MAX_CASH = 2147483647;
}
