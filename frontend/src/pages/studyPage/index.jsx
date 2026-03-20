import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import TeachingSection from './TeachingSection';
import PracticeSection from './PracticeSection';
import FinishCard from './FinishCard';
import { Loader2 } from 'lucide-react';

export default function StudyPage() {
    const { courseId = 1 } = useParams();
    const userId = localStorage.getItem('chilan_user_id') || 'test-user-id';
    
    const [mode, setMode] = useState('loading');
    const [studyData, setStudyData] = useState(null);

    const initFlow = async () => {
        setMode('loading');
        try {
            const res = await axios.get(`http://127.0.0.1:8000/study/init`, {
                params: { course_id: courseId, user_id: userId }
            });
            setStudyData(res.data.data);
            setMode(res.data.mode);
        } catch (e) { setMode('error'); }
    };

    useEffect(() => { initFlow(); }, [courseId]);

    // 处理课程完成
    const handleLessonComplete = async () => {
        const lessonId = studyData?.lesson_content?.lesson_metadata?.lesson_id;
        if (lessonId) {
            await axios.post(`http://127.0.0.1:8000/study/complete_lesson`, {
                user_id: userId,
                course_id: courseId,
                lesson_id: lessonId // 后端现在去更新 user_progress_of_lessons 表
            });
        }
        initFlow(); // 重新检查进入下一阶段
    };

    if (mode === 'loading') return <div className="flex h-screen items-center justify-center"><Loader2 className="animate-spin" /></div>;
    if (mode === 'completed') return <FinishCard />;

    return (
        <div className="min-h-screen bg-slate-50 py-8">
            {mode === 'teaching' && (
                <TeachingSection 
                    data={studyData.lesson_content} 
                    onStartPractice={() => setMode('practice')} 
                />
            )}
            {(mode === 'practice' || mode === 'review') && (
                <PracticeSection 
                    questions={studyData.pending_items} 
                    isReview={mode === 'review'}
                    onAllDone={handleLessonComplete}
                />
            )}
        </div>
    );
}