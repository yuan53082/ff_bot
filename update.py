import subprocess
import sys

def check_updates():
    """列出目前 requirements.txt 裡的套件可用的更新"""
    try:
        print("🔍 檢查可用套件更新中...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--outdated", "--format=columns"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            print("📦 以下套件有更新可用：")
            print(result.stdout)
            return True
        else:
            print("✅ 所有套件已是最新版本！")
            return False
    except Exception as e:
        print(f"❌ 檢查更新失敗: {e}")
        return False

def upgrade_requirements():
    """自動升級 requirements.txt 內所有套件"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"])
        print("✅ 套件已全部升級完成！")
    except subprocess.CalledProcessError as e:
        print(f"❌ 升級套件失敗: {e}")

if __name__ == "__main__":
    if check_updates():
        confirm = input("你要升級這些套件嗎？(y/n): ").strip().lower()
        if confirm == "y":
            upgrade_requirements()
        else:
            print("❌ 已取消升級。")
