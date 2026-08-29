from pathlib import Path
from pythonforandroid.toolchain import ToolchainCL

def after_apk_build(toolchain: ToolchainCL):
    manifest_file = Path(toolchain._dist.dist_dir) / "src" / "main" / "AndroidManifest.xml"
    manifest = manifest_file.read_text(encoding="utf-8")

    service_xml = '''    <service
        android:name="org.bb.bbv4.BBAccessibilityService"
        android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE"
        android:exported="true"
        android:label="BB Assistant">
        <intent-filter>
            <action android:name="android.accessibilityservice.AccessibilityService" />
        </intent-filter>
        <meta-data
            android:name="android.accessibilityservice"
            android:resource="@xml/accessibility_service_config" />
    </service>
'''
    manifest = manifest.replace('</application>', service_xml + '</application>')
    manifest_file.write_text(manifest, encoding="utf-8")
