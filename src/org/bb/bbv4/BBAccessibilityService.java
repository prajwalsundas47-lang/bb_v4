package org.bb.bbv4;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.graphics.Rect;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import java.util.ArrayList;
import java.util.List;

public class BBAccessibilityService extends AccessibilityService {

    private static final String TAG = "BBAccessibility";
    private static BBAccessibilityService instance;

    public static BBAccessibilityService getInstance() {
        return instance;
    }

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
        Log.d(TAG, "BBAccessibilityService connected");
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        // Intentionally empty - we pull screen state on demand from Python,
        // rather than reacting to every event, to keep this lightweight.
    }

    @Override
    public void onInterrupt() {
        Log.d(TAG, "BBAccessibilityService interrupted");
    }

    public static boolean isReady() {
        return instance != null;
    }

    /**
     * Returns a flat list of visible, meaningful nodes on screen as
     * "text|className|centerX|centerY|clickable" strings, one per node.
     * Python parses this - keeps the JNI boundary to simple strings.
     */
    public List<String> describeScreen() {
        List<String> results = new ArrayList<>();
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) {
            return results;
        }
        collectNodes(root, results);
        return results;
    }

    private void collectNodes(AccessibilityNodeInfo node, List<String> results) {
        if (node == null) return;

        CharSequence text = node.getText();
        CharSequence desc = node.getContentDescription();
        String label = null;
        if (text != null && text.length() > 0) {
            label = text.toString();
        } else if (desc != null && desc.length() > 0) {
            label = desc.toString();
        }

        if (label != null && node.isVisibleToUser()) {
            Rect bounds = new Rect();
            node.getBoundsInScreen(bounds);
            String className = node.getClassName() != null ? node.getClassName().toString() : "unknown";
            String safeLabel = label.replace("|", " ").replace("\n", " ").trim();
            results.add(safeLabel + "|" + className + "|" + bounds.centerX() + "|" + bounds.centerY() + "|" + node.isClickable());
        }

        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                collectNodes(child, results);
                child.recycle();
            }
        }
    }

    /**
     * Finds the first visible node whose text/description contains the
     * given query (case-insensitive) and taps its center point via a
     * gesture. Returns true if a match was found and tapped.
     */
    public boolean clickByText(String query) {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return false;

        AccessibilityNodeInfo match = findNodeByText(root, query.toLowerCase());
        if (match == null) return false;

        Rect bounds = new Rect();
        match.getBoundsInScreen(bounds);
        int x = bounds.centerX();
        int y = bounds.centerY();

        return tap(x, y);
    }

    private AccessibilityNodeInfo findNodeByText(AccessibilityNodeInfo node, String queryLower) {
        if (node == null) return null;

        CharSequence text = node.getText();
        CharSequence desc = node.getContentDescription();
        String combined = ((text != null ? text.toString() : "") + " " +
                            (desc != null ? desc.toString() : "")).toLowerCase();

        if (combined.contains(queryLower) && node.isVisibleToUser()) {
            return node;
        }

        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                AccessibilityNodeInfo result = findNodeByText(child, queryLower);
                if (result != null) {
                    return result;
                }
                child.recycle();
            }
        }
        return null;
    }

    private boolean tap(int x, int y) {
        android.graphics.Path path = new android.graphics.Path();
        path.moveTo(x, y);

        android.accessibilityservice.GestureDescription.StrokeDescription stroke =
                new android.accessibilityservice.GestureDescription.StrokeDescription(path, 0, 50);

        android.accessibilityservice.GestureDescription gesture =
                new android.accessibilityservice.GestureDescription.Builder()
                        .addStroke(stroke)
                        .build();

        return dispatchGesture(gesture, null, null);
    }
              }
