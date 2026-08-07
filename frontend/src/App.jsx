import React, { Suspense, lazy, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import { preloadCoursePage } from './coursePageLoader';

// 导入组件
import Navbar from './components/Navbar';
import AppErrorBoundary from './components/AppErrorBoundary';
import { getValidToken } from './utils/authStorage';

const Home = lazy(() => import('./pages/Home'));
const Auth = lazy(() => import('./pages/auth'));
const Learning_Overview = lazy(() => import('./pages/Learning_Overview'));
const Personal_Setting = lazy(() => import('./pages/personalSetting'));
const Classroom = lazy(() => import('./pages/Classroom'));
const StudyPage = lazy(() => import('./pages/studyPage/index.jsx'));
const ExplanationTemplatePreview = lazy(() => import('./pages/ExplanationTemplatePreview'));
const LocalTeachingPreview = lazy(() => import('./pages/LocalTeachingPreview'));
const CourseMaintenance = lazy(() => import('./pages/CourseMaintenance'));
const CourseSync = lazy(() => import('./pages/CourseSync'));
const ContentBuilderConsole = lazy(() => import('./pages/ContentBuilderConsole'));
const DevTools = lazy(() => import('./pages/DevTools'));
const CourseFoundationPage = lazy(() => import('./pages/CourseFoundationPage'));
const CourseSlugPage = lazy(() => import('./pages/CourseSlugPage'));
const CourseStudySlugPage = lazy(() => import('./pages/CourseStudySlugPage'));
const LegacyFoundationRedirect = lazy(() => import('./pages/LegacyFoundationRedirect'));

const CoursePage = lazy(preloadCoursePage);

const ProtectedRoute = ({ children }) => {
  const token = getValidToken();
  return token ? children : <Navigate to="/auth" />;
};

const RouteFallback = () => (
  <main className="min-h-screen bg-slate-50 pt-28 px-6">
    <div className="mx-auto h-48 max-w-5xl animate-pulse rounded-3xl bg-white shadow-sm ring-1 ring-slate-100" />
  </main>
);

function App() {
  useEffect(() => {
    const API_BASE = import.meta.env.VITE_APP_API_BASE_URL || '';
    fetch(`${API_BASE}/health`).catch(() => {});
  }, []);

  return (
    <Router>
      {/* 核心改动：Navbar 放在这里，它将出现在每一个页面顶部 */}
      <Navbar /> 

      <AppErrorBoundary>
        <Suspense fallback={<RouteFallback />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/auth" element={<Auth />} />
            <Route path="/register" element={<Auth />} />
            <Route path="/login" element={<Auth />} />

            {/* 受保护路由 */}
            <Route path="/classroom" element={<ProtectedRoute><Classroom /></ProtectedRoute>} />
            <Route path="/overview" element={<ProtectedRoute><Learning_Overview /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><Personal_Setting /></ProtectedRoute>} />
            <Route path="/course/:courseId" element={<ProtectedRoute><CoursePage /></ProtectedRoute>} />
            <Route path="/courses/:courseSlug" element={<ProtectedRoute><CourseSlugPage /></ProtectedRoute>} />
            <Route path="/study/:courseId" element={<ProtectedRoute><StudyPage /></ProtectedRoute>} />
            <Route path="/courses/:courseSlug/study" element={<ProtectedRoute><CourseStudySlugPage /></ProtectedRoute>} />
            <Route path="/courses/:courseSlug/foundations/:moduleKey" element={<ProtectedRoute><CourseFoundationPage /></ProtectedRoute>} />
            <Route path="/learn/:moduleKey" element={<ProtectedRoute><LegacyFoundationRedirect /></ProtectedRoute>} />
            <Route path="/video-template-preview/:courseId" element={<ExplanationTemplatePreview />} />
            <Route path="/dev" element={<DevTools />} />
            <Route path="/dev/teaching-preview" element={<LocalTeachingPreview />} />
            <Route path="/dev/course-maintenance" element={<CourseMaintenance />} />
            <Route path="/dev/course-sync" element={<CourseSync />} />
            <Route path="/dev/content-builder" element={<ContentBuilderConsole />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </Suspense>
      </AppErrorBoundary>
    </Router>
  );
}

export default App;
