package humblePhlipperNet.dreambot;

import humblePhlipperNet.controllers.Session;

import org.dreambot.api.input.Mouse;
import org.dreambot.api.randoms.RandomSolver;
import org.dreambot.api.script.AbstractScript;
import org.dreambot.api.script.Category;
import org.dreambot.api.script.ScriptManifest;

import java.awt.*;

@ScriptManifest(category = Category.MONEYMAKING, name = "humblePhlipperNet", author = "apnasus", version = 1.00)
public class Main extends AbstractScript {
    private static Session session;

    @Override
    public void onStart(java.lang.String... params) {
        session = new Session(new DreamBot(), params);
    }

    @Override
    public void onStart() {
        Mouse.setMouseAlgorithm(new SmartMouseMultiDir());
        session = new Session(new DreamBot());
    }

    @Override
    public void onSolverEnd(RandomSolver solver){
    }

    @Override
    public void onPaint(Graphics g) {
        if (session == null || session.paint == null) {return;}
        session.paint.onPaint(g);
    }

    @Override
    public void onPause() {
    }

    public void onResume() {
    }

    @Override
    public int onLoop() {
        session.onLoop();
        return 1;
    }

    @Override
    public void onExit() {
        session.onExit();
    }
}