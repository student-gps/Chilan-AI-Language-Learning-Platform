import React from 'react';
import DialogueSection from './DialogueSection';
import VocabularySection from './VocabularySection';

export default function ChineseLessonReference({
    fadeInUp,
    lessonHeading,
    contentType,
    isReadingMode,
    lessonMetadata,
    lineItems,
    diagPinyin,
    setDiagPinyin,
    diagTrans,
    setDiagTrans,
    playingKey,
    activeLessonLineRef,
    playDialogueAudio,
    vocabulary,
    vocabPinyin,
    setVocabPinyin,
    vocabTrans,
    setVocabTrans,
    playTtsFallback,
    targetLanguage,
    readingLabelOn,
    readingLabelOff,
    t,
}) {
    return (
        <>
            <DialogueSection
                fadeInUp={fadeInUp}
                lessonHeading={lessonHeading}
                contentType={contentType}
                isReadingMode={isReadingMode}
                lessonMetadata={lessonMetadata}
                lineItems={lineItems}
                diagPinyin={diagPinyin}
                setDiagPinyin={setDiagPinyin}
                diagTrans={diagTrans}
                setDiagTrans={setDiagTrans}
                playingKey={playingKey}
                activeLessonLineRef={activeLessonLineRef}
                playDialogueAudio={playDialogueAudio}
                targetLanguage={targetLanguage}
                readingLabelOn={readingLabelOn}
                readingLabelOff={readingLabelOff}
                t={t}
            />

            <VocabularySection
                fadeInUp={fadeInUp}
                vocabulary={vocabulary}
                vocabPinyin={vocabPinyin}
                setVocabPinyin={setVocabPinyin}
                vocabTrans={vocabTrans}
                setVocabTrans={setVocabTrans}
                playTtsFallback={playTtsFallback}
                targetLanguage={targetLanguage}
                readingLabelOn={readingLabelOn}
                readingLabelOff={readingLabelOff}
                t={t}
            />
        </>
    );
}
