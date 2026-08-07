export const COURSE_SLUGS = {
    'integrated-chinese-en': 1,
};

export const LEGACY_CHINESE_FOUNDATION_PATHS = {
    intro: '/learn/intro',
    hanzi: '/learn/hanzi',
    pinyin: '/learn/pinyin',
    typing: '/learn/typing',
};

export const buildCoursePath = (course) => {
    const slug = typeof course === 'string' ? course : course?.slug;
    const id = typeof course === 'object' ? course?.id : null;
    return slug ? `/courses/${slug}` : `/course/${id}`;
};

export const buildStudyPath = (course, search = '') => {
    const slug = typeof course === 'string' ? course : course?.slug;
    const id = typeof course === 'object' ? course?.id : null;
    return `${slug ? `/courses/${slug}/study` : `/study/${id}`}${search}`;
};

export const buildFoundationPath = (course, moduleKey) => {
    const slug = typeof course === 'string' ? course : course?.slug;
    if (!slug) return LEGACY_CHINESE_FOUNDATION_PATHS[moduleKey] || '/classroom';
    return `/courses/${slug}/foundations/${moduleKey}`;
};

export const getLegacyFoundationTarget = (moduleKey) =>
    buildFoundationPath('integrated-chinese-en', moduleKey);
