import time
from typing import Dict

class PerformanceMonitor:
    # 全局开关，方便在不需要监控时关闭所有记录逻辑，避免性能损耗
    ENABLED = True

    def __init__(self):
        self.stages: Dict[str, float] = {}
        self.start_time = time.perf_counter()

    def record(self, stage_name: str, duration: float):
        """记录某个阶段的耗时"""
        if not self.ENABLED: return
        self.stages[stage_name] = duration

    def report(self, vector_score: float = None):
        """生成最终的性能报告"""
        if not self.ENABLED: return # 开关检查
        total = time.perf_counter() - self.start_time
        print("\n" + "🏁 " + "—"*20 + " AI 判题全链路报告 " + "—"*20)
        
        if vector_score is not None:
            print(f"🎯 [语义分析] 向量相似度得分: {vector_score:.4f}")
            print("—"*54)

        for name, dur in self.stages.items():
            percentage = (dur / total) * 100 if total > 0 else 0
            # 2026 风格标识
            icon = "🔴" if dur > 1.2 else "🟡" if dur > 0.4 else "🟢"
            # 注意这里：内部使用了单引号 'stage_name'
            print(f"{icon} {name:<18}: {dur:.4f}s ({percentage:>5.1f}%)")
        
        # 🌟 修复位置：这里把 "TOTAL TOTAL" 换成单引号 'TOTAL TOTAL'
        print(f"⌛ {'TOTAL TOTAL':<18}: {total:.4f}s")
        print("—"*54 + "\n")