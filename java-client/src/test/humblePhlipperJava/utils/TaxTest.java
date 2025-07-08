package humblePhlipperJava.utils;

import org.junit.Test;
import static org.junit.Assert.*;

public class TaxTest {
    private static final int OLD_SCHOOL_BOND_ID = 13190;
    private static final int DEATH_RUNE_ID = 560;

    @Test
    public void exemptItemInt() {
        assertEquals(1000, Tax.getPostTaxPrice(OLD_SCHOOL_BOND_ID, 1000));
    }

    @Test
    public void exemptItemDouble() {
        assertEquals(1000.0, Tax.getPostTaxPrice(OLD_SCHOOL_BOND_ID, 1000), 0.000001);
    }

    @Test
    public void cheapInt() {
        assertEquals(49, Tax.getPostTaxPrice(DEATH_RUNE_ID, 49));
    }

    @Test
    public void cheapDouble() {
        assertEquals(49, Tax.getPostTaxPrice(DEATH_RUNE_ID, 49), 0.000001);
    }

    @Test
    public void normalInt() {
        assertEquals(147, Tax.getPostTaxPrice(DEATH_RUNE_ID, 150));
    }

    @Test
    public void normalDouble() {
        assertEquals(147.0, Tax.getPostTaxPrice(DEATH_RUNE_ID, 150.0), 0.000001);
    }

    @Test
    public void expensiveInt() {
        assertEquals(995000000, Tax.getPostTaxPrice(DEATH_RUNE_ID, 1000000000));
    }

    @Test
    public void expensiveDouble() {
        assertEquals(995000000.0, Tax.getPostTaxPrice(DEATH_RUNE_ID, 1000000000), 0.000001);
    }
}
