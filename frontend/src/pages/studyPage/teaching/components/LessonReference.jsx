import React from 'react';
import ChineseLessonReference from './ChineseLessonReference';
import JapaneseLessonReference from './JapaneseLessonReference';

const asArray = (value) => (Array.isArray(value) ? value : []);

const normalizeText = (value = '') => String(value || '').trim().toLowerCase();

const hasMnnShape = (courseContent = {}) => (
    asArray(courseContent.sentence_patterns).length > 0 ||
    asArray(courseContent.example_sentences).length > 0 ||
    asArray(courseContent.dialogue?.lines).length > 0 ||
    asArray(courseContent.display_only_vocabulary).length > 0
);

export const inferLessonReferenceLanguage = ({ data, courseContent, lessonMetadata, courseInfo, courseId, targetLanguage }) => {
    const explicit = normalizeText(targetLanguage);
    if (explicit === 'ja' || explicit === 'jp' || explicit.includes('japanese') || explicit.includes('日本')) return 'ja';

    const metadataTarget = normalizeText(lessonMetadata?.target_language);
    if (metadataTarget === 'ja' || metadataTarget === 'jp' || metadataTarget.includes('japanese') || metadataTarget.includes('日本')) return 'ja';

    const courseTarget = normalizeText(courseInfo?.target_language || courseInfo?.language);
    const category = normalizeText(courseInfo?.category);
    const pipelineId = normalizeText(data?.pipeline_id || lessonMetadata?.pipeline_id);
    const courseSlug = normalizeText(lessonMetadata?.course_slug);
    const id = normalizeText(courseId || lessonMetadata?.course_id || courseInfo?.course_id || courseInfo?.id);
    const source = lessonMetadata?.source || {};
    const textbook = normalizeText(`${source?.textbook || ''} ${source?.textbook_ja || ''} ${source?.textbook_zh || ''}`);

    if (
        id === '303' ||
        category === 'cn_to_ja' ||
        courseTarget.includes('japanese') ||
        courseTarget.includes('日本') ||
        pipelineId.includes('minna') ||
        courseSlug.includes('minna') ||
        textbook.includes('minna') ||
        textbook.includes('みんな') ||
        hasMnnShape(courseContent)
    ) {
        return 'ja';
    }

    if (explicit === 'zh' || explicit.startsWith('zh-') || explicit.includes('chinese') || explicit.includes('中文')) return 'zh';

    return 'zh';
};

export default function LessonReference(props) {
    const referenceLanguage = inferLessonReferenceLanguage(props);

    if (referenceLanguage === 'ja') {
        return (
            <JapaneseLessonReference
                courseContent={props.courseContent}
                lessonMetadata={props.lessonMetadata}
                fadeInUp={props.fadeInUp}
                playingKey={props.playingKey}
                audioLoadingKey={props.audioLoadingKey}
                activeLessonLineRef={props.activeLessonLineRef}
                playTextAudio={(text, key) => props.playTtsFallback?.(text, key, 'ja')}
            />
        );
    }

    return <ChineseLessonReference {...props} />;
}
