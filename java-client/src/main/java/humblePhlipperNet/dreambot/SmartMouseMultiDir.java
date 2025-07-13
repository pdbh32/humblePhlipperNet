package humblePhlipperNet.dreambot;

import org.dreambot.api.Client;
import org.dreambot.api.input.Mouse;
import org.dreambot.api.input.mouse.algorithm.MouseAlgorithm;
import org.dreambot.api.input.mouse.destination.AbstractMouseDestination;
import org.dreambot.api.input.event.impl.mouse.MouseButton;
import org.dreambot.api.script.ScriptManager;
import org.dreambot.api.utilities.Logger;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

import java.awt.Point;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.awt.Canvas;

public class SmartMouseMultiDir implements MouseAlgorithm {
    Canvas canvas = Client.getCanvas();
    int screenWidth = canvas.getWidth();
    int screenHeight = canvas.getHeight();

    private static final int[] DISTANCE_THRESHOLDS = {12, 18, 26, 39, 58, 87, 130, 190, 260, 360, 500};

    private static final double[][] BASE_SPEED_RANGES = {
            {0.005, 0.007},
            {0.007, 0.010},
            {0.010, 0.013}
    };

    private static final double SPEED_VARIANCE = 0.05;

    private static final List<WeightedEasing> SHORT_EASINGS = Arrays.asList(
            new WeightedEasing(EasingFunction.EASE_OUT_CUBIC, 0.4),
            new WeightedEasing(EasingFunction.EASE_IN_OUT_CUBIC, 0.2),
            new WeightedEasing(EasingFunction.EASE_LINEAR, 0.1)
    );

    private static final List<WeightedEasing> MEDIUM_EASINGS = Arrays.asList(
            new WeightedEasing(EasingFunction.EASE_OUT_CUBIC, 0.3),
            new WeightedEasing(EasingFunction.EASE_IN_OUT_CUBIC, 0.2),
            new WeightedEasing(EasingFunction.EASE_LINEAR, 0.1)
    );

    private static final List<WeightedEasing> LONG_EASINGS = Arrays.asList(
            new WeightedEasing(EasingFunction.EASE_IN_OUT_CUBIC, 0.2),
            new WeightedEasing(EasingFunction.EASE_LINEAR, 0.1)
    );

    private Map<String, Object> mouseData;
    private final Random random = new Random();
    private boolean lastActionWasRightClick = false;

    public SmartMouseMultiDir() {
        loadMouseData();
    }

    @Override
    public boolean handleClick(MouseButton mouseButton) {
        boolean result = Mouse.getDefaultMouseAlgorithm().handleClick(mouseButton);

        if (mouseButton == MouseButton.RIGHT_CLICK) {
            lastActionWasRightClick = true;
            sleep(randomDouble(111, 222));
        } else {
            lastActionWasRightClick = false;
        }

        return result;
    }

    @Override
    public boolean handleMovement(AbstractMouseDestination destination) {
        if (!ScriptManager.getScriptManager().isRunning()) {
            // Logger.log("Script stopped; not moving mouse.");
            return false;
        }

        Point target = destination.getSuitablePoint();
        Point current = Mouse.getPosition();

        if (current.equals(target)) {
            // Logger.log("Current mouse position is already at target. No movement needed.");
            return true;
        }

        if (!isWithinCanvas(current) && !isWithinCanvas(target)) {
            // Logger.log("Mouse position and target is outside the client canvas. Skipping path-based movement and hopping.");
            Point outside_exit = Mouse.getPointOutsideScreen();
            Mouse.hop(outside_exit);
            Mouse.setPosition(target.x, target.y);
            return true;
        }

        double distance = distance(current, target);
        // Logger.log("handleMovement => Current: " + current + ", Target: " + target + ", Distance: " + distance);

        double dx = target.getX() - current.getX();
        double dy = target.getY() - current.getY();
        double angleDeg = Math.toDegrees(Math.atan2(dy, dx));
        String orientation = angleTo8Direction(angleDeg);
        // Logger.log("Orientation determined: " + orientation);

        List<Point> path = generatePath(current, target, distance, orientation);
        // Logger.log("Generated path with " + path.size() + " points.");

        EasingFunction easingFunc = selectEasingFunction(distance);
        // Logger.log("Chosen easing function: " + easingFunc.name() + " for distance: " + distance);

        for (int i = 0; i < path.size(); i++) {
            Point stepPoint = path.get(i);
            double stepDurationSeconds = calculateSleepDuration(i, path.size(), distance, easingFunc);
            moveSmoothly(Mouse.getPosition(), stepPoint, stepDurationSeconds, easingFunc);
        }

        double finalDistance = distance(Mouse.getPosition(), target);
        // Logger.log("Final distance to target after movement: " + finalDistance);

        if (lastActionWasRightClick) {
            sleep(randomDouble(111, 222));
        }

        return finalDistance < 2;
    }

    private boolean isWithinCanvas(Point point) {
        return point.getX() >= 0 && point.getY() >= 0 &&
                point.getX() < screenWidth && point.getY() < screenHeight;
    }

    private String angleTo8Direction(double angleDeg) {
        double a = (angleDeg + 360) % 360;
        if ((a >= 337.5 && a < 360) || (a >= 0 && a < 22.5)) return "E";
        else if (a >= 22.5 && a < 67.5) return "NE";
        else if (a >= 67.5 && a < 112.5) return "N";
        else if (a >= 112.5 && a < 157.5) return "NW";
        else if (a >= 157.5 && a < 202.5) return "W";
        else if (a >= 202.5 && a < 247.5) return "SW";
        else if (a >= 247.5 && a < 292.5) return "S";
        else return "SE";
    }

    private void moveSmoothly(Point start, Point end, double totalMovementSeconds, EasingFunction easingFunc) {
        double dist = start.distance(end);
        int subdivisions = Math.max(5, (int) (dist / 2.5));
        double microSleepMs = (totalMovementSeconds * 1000.0) / subdivisions;

        double sx = start.getX(), sy = start.getY();
        double ex = end.getX(), ey = end.getY();
        double dx = ex - sx, dy = ey - sy;

        for (int i = 1; i <= subdivisions; i++) {
            double t = (double) i / subdivisions;
            double easedFrac = easingFunc.apply(t);
            double ix = sx + dx * easedFrac;
            double iy = sy + dy * easedFrac;
            Mouse.hop(new Point((int) ix, (int) iy));
            sleep(microSleepMs);
        }
    }

    private List<Point> generatePath(Point start, Point target, double distance, String orientation) {
        List<Point> path = new ArrayList<>();
        List<List<Double>> offsets = getPathOffsets(distance, orientation);

        if (offsets == null) {
            // Logger.log("No path offsets found for distance/orientation. Moving directly.");
            path.add(target);
            return path;
        }

        List<Double> xOffsets = offsets.get(0);
        List<Double> yOffsets = offsets.get(1);

        double dx = target.getX() - start.getX();
        double dy = target.getY() - start.getY();
        double totalOffsetX = xOffsets.stream().mapToDouble(Double::doubleValue).sum();
        double totalOffsetY = yOffsets.stream().mapToDouble(Double::doubleValue).sum();

        double adjustedDx = dx - totalOffsetX;
        double adjustedDy = dy - totalOffsetY;
        double sx = start.getX(), sy = start.getY();

        for (int i = 0; i < xOffsets.size(); i++) {
            double t = (i + 1.0) / xOffsets.size();
            double offsetX = 0.0, offsetY = 0.0;
            for (int j = 0; j <= i; j++) {
                offsetX += xOffsets.get(j);
                offsetY += yOffsets.get(j);
            }
            double newX = sx + adjustedDx * t + offsetX;
            double newY = sy + adjustedDy * t + offsetY;
            path.add(new Point((int) newX, (int) newY));
        }

        path.add(target);
        return path;
    }

    @SuppressWarnings("unchecked")
    private List<List<Double>> getPathOffsets(double distance, String direction) {
        String category = getDistanceCategory(distance);
        // Logger.log("getPathOffsets => distance=" + distance + ", category=" + category + ", direction=" + direction);
        Map<String, Object> subMap = (Map<String, Object>) mouseData.get(category);
        if (subMap == null) {
            // Logger.log("No data for distance category: " + category);
            return null;
        }

        List<List<List<Double>>> directionPaths = (List<List<List<Double>>>) subMap.get(direction);
        if (directionPaths == null || directionPaths.isEmpty()) {
            // Logger.log("No paths found in JSON for category=" + category + " / direction=" + direction);
            return null;
        }

        int index = random.nextInt(directionPaths.size());
        List<List<Double>> selectedPath = directionPaths.get(index);
        // Logger.log("Selected path index " + index + " with xOffsets=" + selectedPath.get(0).size() + ", yOffsets=" + selectedPath.get(1).size());
        return selectedPath;
    }

    private double calculateSleepDuration(int step, int totalSteps, double distance, EasingFunction easingFunc) {
        if (totalSteps <= 1) {
            // Logger.log("Total steps <= 1, returning 0.0");
            return 0.0;
        }

        double t = (double) step / (totalSteps - 1);
        double baseSpeed = getBaseSpeed(distance);
        double variedSpeed = addHumanVariance(baseSpeed);
        double factor = easingFunc.apply(t);
        return variedSpeed * (0.8 + 0.1 * factor);
    }

    private double getBaseSpeed(double distance) {
        if (distance <= 100) {
            return randomDouble(BASE_SPEED_RANGES[0][0], BASE_SPEED_RANGES[0][1]);
        } else if (distance <= 250) {
            return randomDouble(BASE_SPEED_RANGES[1][0], BASE_SPEED_RANGES[1][1]);
        } else {
            return randomDouble(BASE_SPEED_RANGES[2][0], BASE_SPEED_RANGES[2][1]);
        }
    }

    private double addHumanVariance(double baseSpeed) {
        double maxDelta = baseSpeed * SPEED_VARIANCE;
        double offset = randomDouble(-maxDelta, maxDelta);
        return baseSpeed + offset;
    }

    private EasingFunction selectEasingFunction(double distance) {
        List<WeightedEasing> candidates;
        if (distance <= 100) candidates = SHORT_EASINGS;
        else if (distance <= 250) candidates = MEDIUM_EASINGS;
        else candidates = LONG_EASINGS;

        double totalWeight = 0;
        for (WeightedEasing we : candidates) totalWeight += we.weight;

        double r = random.nextDouble() * totalWeight;
        for (WeightedEasing we : candidates) {
            r -= we.weight;
            if (r <= 0) return we.function;
        }
        return candidates.get(candidates.size() - 1).function;
    }

    private String getDistanceCategory(double distance) {
        for (int threshold : DISTANCE_THRESHOLDS) {
            if (distance <= threshold) {
                return String.valueOf(threshold);
            }
        }
        return String.valueOf(DISTANCE_THRESHOLDS[DISTANCE_THRESHOLDS.length - 1]);
    }

    private void sleep(double millis) {
        try {
            long ms = Math.round(millis);
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private double randomDouble(double min, double max) {
        return min + (max - min) * random.nextDouble();
    }

    private void loadMouseData() {
        Gson gson = new Gson();
        try (InputStream is = getClass().getResourceAsStream("/mousedata.json")) {
            if (is == null) {
                // Logger.log("Error: mousedata.json not found in resources.");
            } else {
                Reader reader = new InputStreamReader(is);
                mouseData = gson.fromJson(reader, new TypeToken<Map<String, Object>>() {}.getType());
                // Logger.log("Mouse data loaded successfully with keys: " + mouseData.keySet());
            }
        } catch (Exception e) {
            // Logger.log("Error loading mouse data: " + e.getMessage());
        }
    }

    private double distance(Point p1, Point p2) {
        return p1.distance(p2);
    }

    private static class WeightedEasing {
        public EasingFunction function;
        public double weight;
        public WeightedEasing(EasingFunction function, double weight) {
            this.function = function;
            this.weight = weight;
        }
    }

    private enum EasingFunction {
        EASE_LINEAR {
            @Override
            public double apply(double t) { return t; }
        },
        EASE_OUT_CUBIC {
            @Override
            public double apply(double t) { return 1 - Math.pow(1 - t, 3); }
        },
        EASE_IN_OUT_CUBIC {
            @Override
            public double apply(double t) {
                return (t < 0.5) ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
            }
        };
        public abstract double apply(double t);
    }
}
