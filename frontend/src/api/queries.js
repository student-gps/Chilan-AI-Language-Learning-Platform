/**
 * React Query 查询定义
 *
 * 统一管理 queryKey + queryFn + staleTime，避免各页面散写。
 * 使用方式：import { coursesQuery, myCoursesQuery, ... } from '../api/queries'
 */
import apiClient from './apiClient';

// ─── queryKey 常量 ────────────────────────────────────────────────────────────
export const queryKeys = {
  courses:        ()           => ['courses'],
  course:         (courseId)   => ['course', String(courseId)],
  lessons:        (courseId)   => ['lessons', String(courseId)],
  myCourses:      (userId)     => ['my-courses', String(userId)],
  classroomStats: (userId)     => ['classroom-stats', String(userId)],
};

// ─── 查询定义对象（直接传给 useQuery）────────────────────────────────────────
/** 全量课程目录（含 lesson_total / total_items） */
export const coursesQuery = () => ({
  queryKey: queryKeys.courses(),
  queryFn:  () => apiClient.get('/courses').then(r => r.data),
  staleTime: 10 * 60 * 1000,   // 10 分钟：课程目录变化很慢
});

/** 单课信息 */
export const courseQuery = (courseId) => ({
  queryKey: queryKeys.course(courseId),
  queryFn:  () => apiClient.get(`/courses/${courseId}`).then(r => r.data),
  staleTime: 10 * 60 * 1000,
  enabled:  Boolean(courseId),
});

/** 某课程的课时列表 */
export const lessonsQuery = (courseId) => ({
  queryKey: queryKeys.lessons(courseId),
  queryFn:  () => apiClient.get(`/courses/${courseId}/lessons`).then(r => r.data),
  staleTime: 10 * 60 * 1000,   // 10 分钟：课时列表几乎不变
  enabled:  Boolean(courseId),
});

/** 用户已报名课程（含进度、FSRS 掌握数等） */
export const myCoursesQuery = (userId) => ({
  queryKey: queryKeys.myCourses(userId),
  queryFn:  () => apiClient.get(`/my-courses/${userId}`).then(r => r.data),
  staleTime: 60 * 1000,         // 1 分钟：报名状态需要相对新鲜
  enabled:  Boolean(userId),
});

/** 教室今日统计（已复习 / 待复习 / 新学） */
export const classroomStatsQuery = (userId) => ({
  queryKey: queryKeys.classroomStats(userId),
  queryFn:  () => apiClient.get(`/classroom/stats/${userId}`).then(r => r.data),
  staleTime: 30 * 1000,         // 30 秒：今日数据实时性强
  enabled:  Boolean(userId),
});
