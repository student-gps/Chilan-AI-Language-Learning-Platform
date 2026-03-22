# services/study/scheduler.py
from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Any

class FSRSScheduler:
    """
    FSRS (Free Spaced Repetition Scheduler) 核心算法组件
    职责：纯数学逻辑，计算复习间隔与掌握状态。
    """
    def __init__(self):
        self.initial_stability = 0.5
        # 难度调整系数 (4:Easy, 3:Good, 2:Hard, 1:Again)
        self.d_adj = {4: -0.5, 3: -0.2, 2: 0.4, 1: 1.0}

    def calc_next_review(self, current_s: float, current_d: float, rating: Any) -> Tuple[float, float, datetime]:
        """
        计算下一次复习的参数与日期
        :param rating: 用户得分 (预期为 1-4 的整数，但也兼容字符串)
        """
        # 🌟 核心修复：强类型转换，防止 str vs int 报错
        try:
            rating = int(rating)
        except (ValueError, TypeError):
            rating = 2  # 如果转换失败，默认给个“需改进”级别，保证流程不崩

        # 1. 更新难度 (限制在 1.0 - 10.0 之间)
        new_d = max(1.0, min(10.0, float(current_d) + self.d_adj.get(rating, 0.0)))
        
        # 2. 计算权重
        weights = {4: 1.0, 3: 0.8, 2: 0.0, 1: 0.0}
        w = weights.get(rating, 0.0)

        # 3. 计算新稳定性
        if rating >= 3:
            # 成功复习：稳定性增长
            new_s = float(current_s) * (1 + ((11 - new_d) / 5) * w)
        else:
            # 复习失败：重置稳定性
            new_s = self.initial_stability

        # 4. 边界处理与天数计算
        new_s = max(self.initial_stability, new_s)
        interval = max(1, round(new_s))
        
        # 5. 生成下次复习时间 (UTC 格式)
        next_date = datetime.now(timezone.utc) + timedelta(days=interval)
        
        return new_s, new_d, next_date

    def check_mastery(self, history: List[Any]) -> bool:
        """判定掌握度：弹性机制"""
        if not history or len(history) < 5:
            return False
            
        # 确保 history 内部也全是 int
        try:
            recent = [int(r) for r in history[-5:]]
        except (ValueError, TypeError):
            return False
        
        # 1. 不能出现 Again(1) 或 Hard(2)
        if any(r <= 2 for r in recent):
            return False
            
        # 2. Easy (4) 的数量 >= 4
        return recent.count(4) >= 4