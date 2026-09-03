package org.bb.bbv4;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.os.IBinder;

public class ServiceRecordingService extends Service {

    public static final String CHANNEL_ID = "bbv4_recording_channel";
    public static final String ACTION_STOP = "org.bb.bbv4.ACTION_STOP_RECORDING";

    private MediaProjection mediaProjection;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            stopSelf();
            return START_NOT_STICKY;
        }

        Notification notification = new Notification.Builder(this, CHANNEL_ID)
                .setContentTitle("BB V4")
                .setContentText("Recording screen")
                .setSmallIcon(android.R.drawable.presence_video_online)
                .build();

        startForeground(1, notification);

        if (intent != null) {
            int resultCode = intent.getIntExtra("resultCode", -1);
            Intent data = intent.getParcelableExtra("data");
            if (data != null) {
                MediaProjectionManager mgr =
                        (MediaProjectionManager) getSystemService(MEDIA_PROJECTION_SERVICE);
                mediaProjection = mgr.getMediaProjection(resultCode, data);
                // TODO: set up VirtualDisplay + MediaRecorder here using mediaProjection
            }
        }

        return START_STICKY;
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, "Recording", NotificationManager.IMPORTANCE_LOW);
            NotificationManager manager = getSystemService(NotificationManager.class);
            manager.createNotificationChannel(channel);
        }
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        if (mediaProjection != null) {
            mediaProjection.stop();
        }
        super.onDestroy();
    }
}
