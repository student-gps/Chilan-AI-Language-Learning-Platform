let activeAudio = null;

const safeReset = (audio, resetCurrentTime = true) => {
    if (!audio) return;
    try {
        audio.pause();
    } catch (_) {
        // no-op
    }
    if (resetCurrentTime) {
        try {
            audio.currentTime = 0;
        } catch (_) {
            // no-op
        }
    }
};

export const claimGlobalAudio = (audio, { resetPrevious = true } = {}) => {
    if (!audio) return;
    if (activeAudio && activeAudio !== audio) {
        safeReset(activeAudio, resetPrevious);
    }
    activeAudio = audio;
};

export const stopGlobalAudio = ({ resetCurrentTime = true } = {}) => {
    if (!activeAudio) return;
    const current = activeAudio;
    activeAudio = null;
    safeReset(current, resetCurrentTime);
};

export const releaseGlobalAudio = (audio) => {
    if (activeAudio === audio) {
        activeAudio = null;
    }
};

export const isGlobalAudioActive = (audio) => activeAudio === audio;
