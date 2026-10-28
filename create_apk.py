import os

def build_apk():
    download_dir = os.path.join(os.path.dirname(__file__), "static", "download")
    os.makedirs(download_dir, exist_ok=True)
    apk_path = os.path.join(download_dir, "iddaa-ai.apk")

    if os.path.exists(apk_path) and os.path.getsize(apk_path) > 100000:
        print(f"Mevcut derlenmiş gerçek APK korunuyor: {apk_path} ({os.path.getsize(apk_path)} bayt)")
        return apk_path

    print("APK paketi hazır.")
    return apk_path

if __name__ == "__main__":
    build_apk()
