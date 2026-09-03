package org.bb.bbv4;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.ContentValues;
import android.content.Intent;
import android.hardware.display.VirtualDisplay;
import android.media.MediaRecorder;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.net.Uri;
import android.os.Build;
import android.os.IBinder;
import android.os.ParcelFileDescriptor;
import android.provider.MediaStore;
import android.util.DisplayMetrics;

import java.io.IOException;

public class ServiceRecordingService extends Service {

    public static final String CHANNEL_ID = "bbv4_recording_channel";
    public static final String ACTION_STOP = "org.bb.bbv4.ACTION_STOP_RECORDING";

    private MediaProjection mediaProjection;
    private VirtualDisplay virtualDisplay;
    private MediaRecorder mediaRecorder;
    private ParcelFileDescriptor outputFd;
    private Uri outputUri;

    private int width, height, fps, bitrate;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            stopRecording();
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
            int resultCode = intent.getIntExtra("projection_result_code", -1);
            Intent data = intent.getParcelableExtra("projection_result_data");

            width = intent.getIntExtra("width", 0);
            height = intent.getIntExtra("height", 0);
            fps = intent.getIntExtra("fps", 30);
            bitrate = intent.getIntExtra("bitrate", 8_000_000);

            if (width <= 0 || height <= 0) {
                DisplayMetrics dm = getResources().getDisplayMetrics();
                width = dm.widthPixels;
                height = dm.heightPixels;
            }

            if (data != null) {
                MediaProjectionManager mgr =
                        (MediaProjectionManager) getSystemService(MEDIA_PROJECTION_SERVICE);
                mediaProjection = mgr.getMediaProjection(resultCode, data);
                startRecording();
            }
        }

        return START_STICKY;
    }

    private void startRecording() {
        try {
            outputUri = createOutputUri();
            outputFd = getContentResolver().openFileDescriptor(outputUri, "rw");

            mediaRecorder = new MediaRecorder();
            mediaRecorder.setVideoSource(MediaRecorder.VideoSource.SURFACE);
            mediaRecorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);
            mediaRecorder.setVideoEncoder(MediaRecorder.VideoEncoder.H264);
            mediaRecorder.setVideoSize(width, height);
            mediaRecorder.setVideoFrameRate(fps);
            mediaRecorder.setVideoEncodingBitRate(bitrate);
            mediaRecorder.setOutputFile(outputFd.getFileDescriptor());
            mediaRecorder.prepare();

            virtualDisplay = mediaProjection.createVirtualDisplay(
                    "BBV4Recording",
                    width, height, getResources().getDisplayMetrics().densityDpi,
                    android.hardware.display.DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                    mediaRecorder.getSurface(), null, null);

            mediaRecorder.start();
        } catch (IOException e) {
            e.printStackTrace();
            stopSelf();
        }
    }

    private Uri createOutputUri() {
        ContentValues values = new ContentValues();
        String filename = "BBV4_" + System.currentTimeMillis() + ".mp4";
        values.put(MediaStore.Video.Media.DISPLAY_NAME, filename);
        values.put(MediaStore.Video.Media.MIME_TYPE, "video/mp4");
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            values.put(MediaStore.Video.Media.RELATIVE_PATH, "Movies/BBV4");
            values.put(MediaStore.Video.Media.IS_PENDING, 1);
        }
        return getContentResolver().insert(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, values);
    }

    private void stopRecording() {
        try {
            if (mediaRecorder != null) {
                mediaRecorder.stop();
                mediaRecorder.reset();
                mediaRecorder.release();
                mediaRecorder = null;
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        if (virtualDisplay != null) {
            virtualDisplay.release();
            virtualDisplay = null;
        }

        if (mediaProjection != null) {
            mediaProjection.stop();
            mediaProjection = null;
        }

        if (outputFd != null) {
            try { outputFd.close(); } catch (IOException ignored) {}
            outputFd = null;
        }

        if (outputUri != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ContentValues values = new ContentValues();
            values.put(MediaStore.Video.Media.IS_PENDING, 0);
            getContentResolver().update(outputUri, values, null, null);
        }
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
        stopRecording();
        super.onDestroy();
    }
                }
