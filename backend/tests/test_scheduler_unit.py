"""
Unit tests for FSRSScheduler — pure math, no DB or network.
覆盖复习间隔计算与掌握度判定的边界条件，改动算法时这里会先报警。
"""
import unittest
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.study.scheduler import FSRSScheduler


class TestCalcNextReview(unittest.TestCase):
    def setUp(self):
        self.sch = FSRSScheduler()

    # ── 基本方向 ──────────────────────────────────
    def test_easy_rating_increases_stability(self):
        s0, d0 = 1.0, 5.0
        new_s, new_d, _ = self.sch.calc_next_review(s0, d0, rating=4)
        self.assertGreater(new_s, s0)

    def test_good_rating_increases_stability(self):
        s0, d0 = 1.0, 5.0
        new_s, _, _ = self.sch.calc_next_review(s0, d0, rating=3)
        self.assertGreater(new_s, s0)

    def test_hard_rating_resets_stability(self):
        s0, d0 = 5.0, 5.0
        new_s, _, _ = self.sch.calc_next_review(s0, d0, rating=2)
        self.assertEqual(new_s, self.sch.initial_stability)

    def test_again_rating_resets_stability(self):
        s0, d0 = 5.0, 5.0
        new_s, _, _ = self.sch.calc_next_review(s0, d0, rating=1)
        self.assertEqual(new_s, self.sch.initial_stability)

    # ── 难度更新 ──────────────────────────────────
    def test_easy_decreases_difficulty(self):
        _, new_d, _ = self.sch.calc_next_review(1.0, 5.0, rating=4)
        self.assertLess(new_d, 5.0)

    def test_again_increases_difficulty(self):
        _, new_d, _ = self.sch.calc_next_review(1.0, 5.0, rating=1)
        self.assertGreater(new_d, 5.0)

    def test_difficulty_lower_bound(self):
        # 再简单也不能低于 1.0
        _, new_d, _ = self.sch.calc_next_review(1.0, 1.0, rating=4)
        self.assertGreaterEqual(new_d, 1.0)

    def test_difficulty_upper_bound(self):
        # 再难也不能超过 10.0
        _, new_d, _ = self.sch.calc_next_review(1.0, 10.0, rating=1)
        self.assertLessEqual(new_d, 10.0)

    # ── 返回值类型 ────────────────────────────────
    def test_returns_three_values(self):
        result = self.sch.calc_next_review(1.0, 5.0, rating=3)
        self.assertEqual(len(result), 3)

    def test_next_date_is_utc_datetime(self):
        _, _, next_date = self.sch.calc_next_review(1.0, 5.0, rating=3)
        self.assertIsInstance(next_date, datetime)
        self.assertEqual(next_date.tzinfo, timezone.utc)

    def test_next_date_is_in_future(self):
        _, _, next_date = self.sch.calc_next_review(1.0, 5.0, rating=3)
        self.assertGreater(next_date, datetime.now(timezone.utc))

    def test_stability_never_below_initial(self):
        # 即使连续失败，稳定性不应低于初始值
        new_s, _, _ = self.sch.calc_next_review(0.1, 5.0, rating=1)
        self.assertGreaterEqual(new_s, self.sch.initial_stability)

    # ── 容错：非整数 rating ────────────────────────
    def test_string_rating_coerced(self):
        new_s, new_d, _ = self.sch.calc_next_review(1.0, 5.0, rating="3")
        self.assertIsInstance(new_s, float)
        self.assertIsInstance(new_d, float)

    def test_invalid_rating_falls_back_gracefully(self):
        # 无效值不应抛异常，应有合理输出
        new_s, new_d, _ = self.sch.calc_next_review(1.0, 5.0, rating="bad")
        self.assertIsInstance(new_s, float)
        self.assertIsInstance(new_d, float)

    def test_none_rating_falls_back_gracefully(self):
        new_s, new_d, _ = self.sch.calc_next_review(1.0, 5.0, rating=None)
        self.assertIsInstance(new_s, float)

    # ── 高稳定性 → 更长间隔 ───────────────────────
    def test_higher_stability_gives_longer_interval(self):
        _, _, date_low = self.sch.calc_next_review(1.0, 5.0, rating=4)
        _, _, date_high = self.sch.calc_next_review(10.0, 5.0, rating=4)
        self.assertGreater(date_high, date_low)


# ─────────────────────────────────────────────
# check_mastery
# ─────────────────────────────────────────────
class TestCheckMastery(unittest.TestCase):
    def setUp(self):
        self.sch = FSRSScheduler()

    def test_all_easy_is_mastered(self):
        self.assertTrue(self.sch.check_mastery([4, 4, 4, 4, 4]))

    def test_four_easy_one_good_is_mastered(self):
        # [3, 4, 4, 4, 4] → Easy >= 4，无 Again/Hard，应通过
        self.assertTrue(self.sch.check_mastery([3, 4, 4, 4, 4]))

    def test_all_good_is_not_mastered(self):
        # 全部 Good(3)，Easy 数量不足 4
        self.assertFalse(self.sch.check_mastery([3, 3, 3, 3, 3]))

    def test_one_hard_blocks_mastery(self):
        self.assertFalse(self.sch.check_mastery([2, 4, 4, 4, 4]))

    def test_one_again_blocks_mastery(self):
        self.assertFalse(self.sch.check_mastery([1, 4, 4, 4, 4]))

    def test_fewer_than_5_reviews_not_mastered(self):
        self.assertFalse(self.sch.check_mastery([4, 4, 4, 4]))

    def test_empty_history_not_mastered(self):
        self.assertFalse(self.sch.check_mastery([]))

    def test_none_history_not_mastered(self):
        self.assertFalse(self.sch.check_mastery(None))

    def test_only_last_5_matter(self):
        # 前面很多次失败，只要最后 5 次满足条件就算掌握
        long_history = [1, 1, 1, 2, 1] + [4, 4, 4, 4, 4]
        self.assertTrue(self.sch.check_mastery(long_history))

    def test_last_5_bad_despite_good_earlier(self):
        long_history = [4, 4, 4, 4, 4] + [1, 1, 1, 1, 1]
        self.assertFalse(self.sch.check_mastery(long_history))

    def test_string_ratings_in_history(self):
        # 历史记录中可能混有字符串类型
        self.assertTrue(self.sch.check_mastery(["4", "4", "4", "4", "4"]))

    def test_invalid_history_values_not_mastered(self):
        self.assertFalse(self.sch.check_mastery(["x", "y", "z", "a", "b"]))


if __name__ == "__main__":
    unittest.main()
