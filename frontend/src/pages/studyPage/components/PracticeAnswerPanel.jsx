import React from 'react';
import SpeechAnswerPanel from './SpeechAnswerPanel';
import TextAnswerPanel from './TextAnswerPanel';

export default function PracticeAnswerPanel(props) {
    if (props.speechMode) {
        return <SpeechAnswerPanel {...props} />;
    }

    return <TextAnswerPanel {...props} />;
}
