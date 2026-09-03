package org.bb.bbv4;

import android.app.Service;
import android.content.Intent;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.IBinder;
import android.view.Gravity;
import android.view.WindowManager;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.os.Handler;
import android.os.Looper;

public class FloatingControlService extends Service {

    private WindowManager windowManager;
    private LinearLayout floatingView;
    private TextView timerText;
    private Handler handler = new Handler(Looper.getMainLooper());
    private long startTime;
    private boolean running = false;

    @Override
    public void onCreate() {
        super.onCreate();
        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);

        floatingView = new LinearLayout(this);
        floatingView.setOrientation(LinearLayout.HORIZONTAL);
        floatingView.setBackgroundColor(0xAA000000);
        floatingView.setPadding(24, 12, 24, 12);

        timerText = new TextView(this);
        timerText.setText("00:00");
        timerText.setTextColor(0xFFFFFFFF);
        timerText.setTextSize(16);
        floatingView.addView(timerText);

        TextView stopBtn = new TextView(this);
        stopBtn.setText("  ⏹ STOP  ");
        stopBtn.setTextColor(0xFFFF4444);
        stopBtn.setTextSize(16);
        stopBtn.setOnClickListener(v -> {
            Intent stopIntent = new Intent(this, ServiceRecordingService.class);
            stopIntent.setAction(ServiceRecordingService.ACTION_STOP);
            startService(stopIntent);
            stopSelf();
        });
        floatingView.addView(stopBtn);

        int overlayType = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                : WindowManager.LayoutParams.TYPE_PHONE;

        WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                overlayType,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                PixelFormat.TRANSLUCENT);
        params.gravity = Gravity.TOP | Gravity.END;
        params.x = 16;
        params.y = 100;

        windowManager.addView(floatingView, params);

        startTime = System.currentTimeMillis();
        running = true;
        handler.post(updateTimer);
    }

    private final Runnable updateTimer = new Runnable() {
        @Override
        public void run() {
            if (!running) return;
            long elapsed = (System.currentTimeMillis() - startTime) / 1000;
            timerText.setText(String.format("%02d:%02d", elapsed / 60, elapsed % 60));
            handler.postDelayed(this, 1000);
        }
    };

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        return START_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        running = false;
        if (floatingView != null) windowManager.removeView(floatingView);
        super.onDestroy();
    }
              }
