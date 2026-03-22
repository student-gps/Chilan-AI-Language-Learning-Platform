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
            const { mode: responseMode, data } = res.data;
            setStudyData(data);
            
            if (responseMode === 'teaching' && data.skip_content) {
                setMode('practice');
            } else {
                setMode(responseMode);
            }
        } catch (e) { 
            console.error(e);
            setMode('error'); 
        }
    };

    useEffect(() => { initFlow(); }, [courseId]);

    // 🌟 修改：完成练习后，只推进度，不立刻进下一课
    const handleLessonComplete = async () => {
        const lessonId = studyData?.lesson_content?.lesson_metadata?.lesson_id;
        
        // 如果是从新课 (practice) 过来的，更新总体进度
        if (lessonId && mode === 'practice') {
            await axios.post(`http://127.0.0.1:8000/study/complete_lesson`, {
                user_id: userId,
                course_id: courseId,
                lesson_id: lessonId 
            });
        }
        
        // 核心：切到胜利结算页！
        setMode('lesson_finished'); 
    };

    if (mode === 'loading') return <div className="flex h-screen items-center justify-center"><Loader2 className="animate-spin text-blue-500" size={32} /></div>;
    
    // 🌟 全部结束：只有回主页按钮
    if (mode === 'completed') return <FinishCard isAllCompleted={true} />;
    
    // 🌟 单课结束：出现“继续下一课”按钮，点击后触发 initFlow
    if (mode === 'lesson_finished') return <FinishCard isAllCompleted={false} onContinue={initFlow} />;

    return (
        <div className="min-h-screen bg-slate-50 py-8">
            {mode === 'teaching' && (
                <TeachingSection 
                    data={studyData.lesson_content} 
                    courseId={courseId} 
                    userId={userId}     
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