import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// 导入组件
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Auth from './pages/auth';
import Learning_Overview from './pages/Learning_Overview';
import Personal_Setting from './pages/personalSetting';
import Classroom from './pages/Classroom';
import StudyPage from './pages/studyPage/index.jsx'
import ExplanationTemplatePreview from './pages/ExplanationTemplatePreview';
import PinyinPage from './pages/PinyinPage';
import CourseIntroPage from './pages/CourseIntroPage';
import HanziIntroPage from './pages/HanziIntroPage';
import { getValidToken } from './utils/authStorage';

const ProtectedRoute = ({ children }) => {
  const token = getValidToken();
  return token ? children : <Navigate to="/auth" />;
};

function App() {
  return (
    <Router>
      {/* 核心改动：Navbar 放在这里，它将出现在每一个页面顶部 */}
      <Navbar /> 

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/auth" element={<Auth />} />
        <Route path="/register" element={<Auth />} />
        <Route path="/login" element={<Auth />} />

        {/* 受保护路由 */}
        <Route path="/classroom" element={<ProtectedRoute><Classroom /></ProtectedRoute>} />
        <Route path="/overview" element={<ProtectedRoute><Learning_Overview /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Personal_Setting /></ProtectedRoute>} />
        <Route path="/study/:courseId" element={<ProtectedRoute><StudyPage /></ProtectedRoute>} />
        <Route path="/video-template-preview/:courseId" element={<ExplanationTemplatePreview />} />
        <Route path="/learn/pinyin" element={<ProtectedRoute><PinyinPage /></ProtectedRoute>} />
        <Route path="/learn/intro" element={<ProtectedRoute><CourseIntroPage /></ProtectedRoute>} />
        <Route path="/learn/hanzi" element={<ProtectedRoute><HanziIntroPage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
