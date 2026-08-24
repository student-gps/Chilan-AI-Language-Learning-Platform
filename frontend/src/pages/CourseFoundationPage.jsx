import { lazy, Suspense, useMemo } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { foundationModulesQuery, courseBySlugQuery } from '../api/queries';
import { buildCoursePath, buildFoundationPath } from '../utils/courseRoutes';

const MODULE_LOADERS = {
    'course-intro-v1': lazy(() => import('./CourseIntroPage')),
    'chinese-hanzi-v1': lazy(() => import('./HanziIntroPage')),
    'chinese-pinyin-v1': lazy(() => import('./PinyinPage')),
    'chinese-ime-v1': lazy(() => import('./TypingIntroPage')),
    'japanese-foundations-v1': lazy(() => import('./japaneseFoundation/JapaneseFoundationPage')),
};

const moduleLabel = (module, t) => t(module.title_key, {
    defaultValue: module.default_title || module.key,
});

function ModuleFallback() {
    return (
        <div className="flex min-h-screen items-center justify-center bg-slate-50 pt-16">
            <div className="h-56 w-full max-w-4xl animate-pulse rounded-3xl bg-white shadow-sm ring-1 ring-slate-100" />
        </div>
    );
}

function CourseFoundationState({ title, body, coursePath }) {
    return (
        <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6 pt-16">
            <section className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
                <h1 className="text-2xl font-black text-slate-900">{title}</h1>
                <p className="mt-3 text-sm font-medium leading-relaxed text-slate-500">{body}</p>
                {coursePath && (
                    <Link
                        to={coursePath}
                        className="mt-6 inline-flex rounded-2xl bg-slate-900 px-5 py-3 text-sm font-black text-white transition hover:bg-blue-600"
                    >
                        Back to course
                    </Link>
                )}
            </section>
        </main>
    );
}

export default function CourseFoundationPage() {
    const { courseSlug, moduleKey } = useParams();
    const navigate = useNavigate();
    const location = useLocation();
    const { t } = useTranslation();
    const { data: course, isLoading: isCourseLoading, isError: isCourseError } = useQuery(courseBySlugQuery(courseSlug));
    const { data: modules = [], isLoading: isModulesLoading } = useQuery(foundationModulesQuery(courseSlug));

    const currentModule = useMemo(
        () => modules.find((item) => item.key === moduleKey),
        [moduleKey, modules]
    );
    const ModulePage = currentModule ? MODULE_LOADERS[currentModule.implementation_key] : null;

    if (isCourseLoading || isModulesLoading) return <ModuleFallback />;
    if (isCourseError || !course) {
        return <CourseFoundationState title="Course not found" body="This course is unavailable or no longer exists." />;
    }
    if (!currentModule) {
        return (
            <CourseFoundationState
                title="Foundation module not found"
                body="This learning foundation is not available for the selected course."
                coursePath={buildCoursePath(course)}
            />
        );
    }
    if (!ModulePage) {
        return (
            <CourseFoundationState
                title="Foundation module is not supported yet"
                body="The course has this module configured, but its learning experience has not been published yet."
                coursePath={buildCoursePath(course)}
            />
        );
    }

    const currentIndex = modules.findIndex((item) => item.key === moduleKey);
    const previousModule = currentIndex > 0 ? modules[currentIndex - 1] : null;
    const nextModule = currentIndex >= 0 && currentIndex < modules.length - 1 ? modules[currentIndex + 1] : null;
    const navigation = {
        coursePath: buildCoursePath(course),
        previous: previousModule && {
            path: buildFoundationPath(course, previousModule.key),
            label: moduleLabel(previousModule, t),
        },
        next: nextModule && {
            path: buildFoundationPath(course, nextModule.key),
            label: moduleLabel(nextModule, t),
        },
    };

    return (
        <Suspense fallback={<ModuleFallback />}>
            <ModulePage
                foundationNavigation={navigation}
                locationState={location.state}
                navigate={navigate}
                course={course}
                foundationModule={currentModule}
            />
        </Suspense>
    );
}
