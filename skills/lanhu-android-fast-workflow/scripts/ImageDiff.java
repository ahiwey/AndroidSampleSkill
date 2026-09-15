import java.awt.AlphaComposite;
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import javax.imageio.ImageIO;

public final class ImageDiff {
    private record Tile(int x, int y, int width, int height, double score) {}
    private record Result(double meanChannelError, double mismatchRatio, long mismatchPixels, long totalPixels) {}

    private static void usage() {
        System.out.println("Usage: java ImageDiff <reference> <actual> <output-dir> [--threshold 12] [--tiles 5]");
    }

    private static String jsonEscape(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private static int channelDiff(int left, int right, int shift) {
        return Math.abs(((left >> shift) & 0xff) - ((right >> shift) & 0xff));
    }

    private static Result compare(
            BufferedImage reference,
            BufferedImage actual,
            BufferedImage heatmap,
            int threshold,
            int startX,
            int startY,
            int width,
            int height) {
        long totalError = 0;
        long mismatch = 0;
        long pixels = (long) width * height;
        for (int y = startY; y < startY + height; y++) {
            for (int x = startX; x < startX + width; x++) {
                int ref = reference.getRGB(x, y);
                int act = actual.getRGB(x, y);
                int da = channelDiff(ref, act, 24);
                int dr = channelDiff(ref, act, 16);
                int dg = channelDiff(ref, act, 8);
                int db = channelDiff(ref, act, 0);
                int max = Math.max(Math.max(da, dr), Math.max(dg, db));
                totalError += (long) da + dr + dg + db;
                if (max > threshold) mismatch += 1;
                if (heatmap != null) {
                    int intensity = Math.min(255, max * 3);
                    heatmap.setRGB(x, y, new Color(intensity, max > threshold ? 24 : 0, 0).getRGB());
                }
            }
        }
        return new Result(totalError / (double) (pixels * 4), mismatch / (double) pixels, mismatch, pixels);
    }

    private static BufferedImage crop(BufferedImage source, Tile tile) {
        BufferedImage result = new BufferedImage(tile.width, tile.height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D graphics = result.createGraphics();
        graphics.drawImage(source, 0, 0, tile.width, tile.height,
                tile.x, tile.y, tile.x + tile.width, tile.y + tile.height, null);
        graphics.dispose();
        return result;
    }

    private static List<Tile> rankedTiles(BufferedImage reference, BufferedImage actual, int threshold, int limit) {
        int columns = 4;
        int rows = Math.max(4, (int) Math.ceil(reference.getHeight() / (reference.getWidth() / 4.0)));
        int tileWidth = (int) Math.ceil(reference.getWidth() / (double) columns);
        int tileHeight = (int) Math.ceil(reference.getHeight() / (double) rows);
        List<Tile> tiles = new ArrayList<>();
        for (int row = 0; row < rows; row++) {
            for (int column = 0; column < columns; column++) {
                int x = column * tileWidth;
                int y = row * tileHeight;
                int width = Math.min(tileWidth, reference.getWidth() - x);
                int height = Math.min(tileHeight, reference.getHeight() - y);
                if (width <= 0 || height <= 0) continue;
                Result result = compare(reference, actual, null, threshold, x, y, width, height);
                tiles.add(new Tile(x, y, width, height, result.mismatchRatio));
            }
        }
        return tiles.stream()
                .filter(tile -> tile.score > 0)
                .sorted(Comparator.comparingDouble(Tile::score).reversed())
                .limit(limit)
                .toList();
    }

    private static String run(Path referencePath, Path actualPath, Path outputDir, int threshold, int tileCount)
            throws IOException {
        BufferedImage reference = ImageIO.read(referencePath.toFile());
        BufferedImage actual = ImageIO.read(actualPath.toFile());
        if (reference == null || actual == null) throw new IOException("Unsupported or unreadable image format");
        if (reference.getWidth() != actual.getWidth() || reference.getHeight() != actual.getHeight()) {
            throw new IllegalArgumentException("Image dimensions differ: reference=" + reference.getWidth() + "x" +
                    reference.getHeight() + ", actual=" + actual.getWidth() + "x" + actual.getHeight());
        }
        Files.createDirectories(outputDir);
        BufferedImage heatmap = new BufferedImage(reference.getWidth(), reference.getHeight(), BufferedImage.TYPE_INT_RGB);
        Result result = compare(reference, actual, heatmap, threshold, 0, 0, reference.getWidth(), reference.getHeight());
        ImageIO.write(heatmap, "png", outputDir.resolve("diff_heatmap.png").toFile());

        BufferedImage overlay = new BufferedImage(reference.getWidth(), reference.getHeight(), BufferedImage.TYPE_INT_ARGB);
        Graphics2D graphics = overlay.createGraphics();
        graphics.drawImage(reference, 0, 0, null);
        graphics.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER, 0.5f));
        graphics.drawImage(actual, 0, 0, null);
        graphics.dispose();
        ImageIO.write(overlay, "png", outputDir.resolve("overlay.png").toFile());

        List<Tile> tiles = rankedTiles(reference, actual, threshold, tileCount);
        StringBuilder tileJson = new StringBuilder("[");
        for (int index = 0; index < tiles.size(); index++) {
            Tile tile = tiles.get(index);
            String stem = String.format("diff_%02d", index + 1);
            ImageIO.write(crop(reference, tile), "png", outputDir.resolve(stem + "_reference.png").toFile());
            ImageIO.write(crop(actual, tile), "png", outputDir.resolve(stem + "_actual.png").toFile());
            ImageIO.write(crop(heatmap, tile), "png", outputDir.resolve(stem + "_heatmap.png").toFile());
            if (index > 0) tileJson.append(',');
            tileJson.append(String.format(
                    "{\"x\":%d,\"y\":%d,\"width\":%d,\"height\":%d,\"mismatch_ratio\":%.6f,\"stem\":\"%s\"}",
                    tile.x, tile.y, tile.width, tile.height, tile.score, stem));
        }
        tileJson.append(']');
        String json = String.format(
                "{\"status\":\"ok\",\"width\":%d,\"height\":%d,\"threshold\":%d," +
                        "\"mean_channel_error\":%.6f,\"mismatch_ratio\":%.6f,\"mismatch_pixels\":%d," +
                        "\"total_pixels\":%d,\"output\":\"%s\",\"top_tiles\":%s}",
                reference.getWidth(), reference.getHeight(), threshold, result.meanChannelError,
                result.mismatchRatio, result.mismatchPixels, result.totalPixels,
                jsonEscape(outputDir.toAbsolutePath().toString()), tileJson);
        Files.writeString(outputDir.resolve("metrics.json"), json + System.lineSeparator());
        return json;
    }

    private static void selfTest() throws IOException {
        Path directory = Files.createTempDirectory("image-diff-self-test-");
        try {
            BufferedImage reference = new BufferedImage(64, 64, BufferedImage.TYPE_INT_ARGB);
            BufferedImage actual = new BufferedImage(64, 64, BufferedImage.TYPE_INT_ARGB);
            Graphics2D refGraphics = reference.createGraphics();
            refGraphics.setColor(Color.WHITE);
            refGraphics.fillRect(0, 0, 64, 64);
            refGraphics.dispose();
            Graphics2D actualGraphics = actual.createGraphics();
            actualGraphics.setColor(Color.WHITE);
            actualGraphics.fillRect(0, 0, 64, 64);
            actualGraphics.setColor(Color.RED);
            actualGraphics.fillRect(16, 16, 16, 16);
            actualGraphics.dispose();
            Path ref = directory.resolve("reference.png");
            Path act = directory.resolve("actual.png");
            ImageIO.write(reference, "png", ref.toFile());
            ImageIO.write(actual, "png", act.toFile());
            String result = run(ref, act, directory.resolve("out"), 12, 3);
            if (!result.contains("\"mismatch_pixels\":256")) throw new IllegalStateException("pixel diff self-test failed");
            System.out.println("{\"status\":\"ok\",\"test\":\"ImageDiff\"}");
        } finally {
            try (var paths = Files.walk(directory)) {
                paths.sorted(Comparator.reverseOrder()).forEach(path -> {
                    try { Files.deleteIfExists(path); } catch (IOException ignored) {}
                });
            }
        }
    }

    public static void main(String[] args) {
        try {
            if (args.length == 1 && args[0].equals("--self-test")) {
                selfTest();
                return;
            }
            if (args.length < 3) {
                usage();
                System.exit(2);
            }
            int threshold = 12;
            int tiles = 5;
            for (int index = 3; index < args.length; index++) {
                if (args[index].equals("--threshold")) threshold = Integer.parseInt(args[++index]);
                else if (args[index].equals("--tiles")) tiles = Integer.parseInt(args[++index]);
                else throw new IllegalArgumentException("Unknown option: " + args[index]);
            }
            System.out.println(run(Path.of(args[0]), Path.of(args[1]), Path.of(args[2]), threshold, tiles));
        } catch (Exception error) {
            System.err.println("{\"status\":\"error\",\"message\":\"" + jsonEscape(error.getMessage()) + "\"}");
            System.exit(1);
        }
    }
}
