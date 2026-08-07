import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { courseBySlugQuery, queryKeys } from '../api/queries';
import StudyPage from './studyPage';

function StudyFallback() {
    return (
        <div className="min-h-screen bg-slate-50 py-8">
            <div className="mx-auto max-w-3xl space-y-6 px-6 pt-8">
                <div className="h-8 w-48 animate-pulse rounded-2xl bg-slate-200" />
                <div className="h-80 animate-pulse rounded-3xl bg-white shadow-sm ring-1 ring-slate-100" />
            </div>
        </div>
    );
}

export default function CourseStudySlugPage() {
    const { courseSlug } = useParams();
    const queryClient = useQueryClient();
    const { data: course, isLoading, isError } = useQuery(courseBySlugQuery(courseSlug));

    useEffect(() => {
        if (course) queryClient.setQueryData(queryKeys.course(course.id), course);
    }, [course, queryClient]);

    if (isLoading) return <StudyFallback />;
    if (isError || !course) {
        return (
            <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6 pt-16">
                <section className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
                    <h1 className="text-2xl font-black text-slate-900">Course not found</h1>
                    <p className="mt-3 text-sm font-medium text-slate-500">This course is unavailable or no longer exists.</p>
                </section>
            </main>
        );
    }

    return <StudyPage resolvedCourseId={course.id} resolvedCourse={course} />;
}
