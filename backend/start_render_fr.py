import time, subprocess, sys
from datetime import datetime, timedelta

DELAY_HOURS = 3
start_at = datetime.now() + timedelta(hours=DELAY_HOURS)
print(f"⏳ 将在 {start_at.strftime('%H:%M:%S')} 开始渲染法语视频（{DELAY_HOURS}h 后）")
print("   按 Ctrl+C 可取消")

try:
    time.sleep(DELAY_HOURS * 3600)
except KeyboardInterrupt:
    print("\n❌ 已取消")
    sys.exit(0)

print(f"\n🚀 [{datetime.now().strftime('%H:%M:%S')}] 开始渲染法语视频...")
result = subprocess.run(
    [sys.executable, "content_builder/render_narration.py", "--render-video", "--lang", "fr"],
    cwd=".",
)
sys.exit(result.returncode)
