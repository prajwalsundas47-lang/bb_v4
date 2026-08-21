class RecordingSettings:
    """Screen-recording configuration with sensible defaults for a phone capture."""

    def __init__(self, width=1080, height=2400, fps=30,
                 bitrate=8_000_000, mime="video/avc", audio_mode="mic"):
        self.width = width
        self.height = height
        self.fps = fps
        self.bitrate = bitrate
        self.mime = mime
        self.audio_mode = audio_mode
