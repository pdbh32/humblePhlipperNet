package humblePhlipperNet.utils;

import org.junit.Test;
import static org.junit.Assert.*;

public class TaxTest {
    private static final int OLD_SCHOOL_BOND_ID = 13190;
    private static final int DEATH_RUNE_ID = 560;

    @Test
    public void exemptItem() {
        assertEquals(1000, Tax.getPostTaxPrice(OLD_SCHOOL_BOND_ID, 1000));
    }

    @Test
    public void cheap() {
        assertEquals(49, Tax.getPostTaxPrice(DEATH_RUNE_ID, 49));
    }

    @Test
    public void normal() {
        assertEquals(147, Tax.getPostTaxPrice(DEATH_RUNE_ID, 150));
    }

    @Test
    public void expensive() {
        assertEquals(995000000, Tax.getPostTaxPrice(DEATH_RUNE_ID, 1000000000));
    }
}
