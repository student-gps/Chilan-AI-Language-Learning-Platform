import { useMemo } from 'react';
import JapaneseCourseIntro from './JapaneseCourseIntro';
import JapaneseKanaBasics from './JapaneseKanaBasics';
import JapanesePronunciation from './JapanesePronunciation';
import JapaneseKanjiBasics from './JapaneseKanjiBasics';
import JapaneseTypingBasics from './JapaneseTypingBasics';
import { useJapaneseAudio } from './FoundationLayout';
import { getFoundationCopy } from './foundationContent';
import { normalizeJapaneseFoundationLanguage } from '../../utils/japaneseFoundationLanguages';

const MODULE_COMPONENTS = {
    intro: JapaneseCourseIntro,
    kana: JapaneseKanaBasics,
    pronunciation: JapanesePronunciation,
    kanji: JapaneseKanjiBasics,
    typing: JapaneseTypingBasics,
};

export default function JapaneseFoundationPage({ course, foundationModule, ...navigationProps }) {
    const supportLanguage = normalizeJapaneseFoundationLanguage(course?.support_language_code);
    const copy = useMemo(() => getFoundationCopy(supportLanguage), [supportLanguage]);
    const audio = useJapaneseAudio(copy.common.audioError);
    const ModuleComponent = MODULE_COMPONENTS[foundationModule?.key] || JapaneseCourseIntro;

    return (
        <ModuleComponent
            {...navigationProps}
            course={course}
            foundationModule={foundationModule}
            supportLanguage={supportLanguage}
            copy={copy}
            audio={audio}
        />
    );
}
