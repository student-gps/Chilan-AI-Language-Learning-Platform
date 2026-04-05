import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Loader2, RefreshCcw, Sparkles } from 'lucide-react';
import WordContextCard from './WordContextCard';

const splitFeedbackParagraphs = (message = '') =>
    String(message)
        .split(/\r?\n+/)
        .map((part) => part.trim())
        .filter(Boolean);

export default function PracticeFeedbackPanel({
    feedback,
    isPerfectFeedback,
    isTypingFeedback,
    typedFeedbackMessage,
    speechMode,
    onRetry,
    onSkip,
    onNext,
    retryDisabled,
    currentIndex,
    totalQuestions,
    isBusy,
    primaryButtonRef,
    actionsRef,
    primaryButtonClass,
    secondaryButtonClass,
    currentQuestion,
    knowledgeDetails,
}) {
    const [activeAction, setActiveAction] = React.useState(feedback.level === 1 ? 'retry' : 'next');

    React.useEffect(() => {
        setActiveAction(feedback.level === 1 ? 'retry' : 'next');
    }, [feedback, currentIndex]);

    const resolveButtonClass = (actionKey) =>
        activeAction === actionKey ? primaryButtonClass : secondaryButtonClass;

    const enterHintClass = (actionKey) =>
        activeAction === actionKey ? 'text-blue-200' : 'text-slate-400';

    const feedbackParagraphs = splitFeedbackParagraphs(typedFeedbackMessage);
    const hasTypingCursor = typedFeedbackMessage.length < (feedback.message || '').length;

    return (
        <motion.div ref={actionsRef} key="feedback-area" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
            {!isPerfectFeedback && (
                <div className="rounded-[2rem] border border-slate-200 bg-slate-50/70 px-6 py-5">
                    <div className="space-y-4">
                        <AnimatePresence initial={false}>
                            {isTypingFeedback && (
                                <motion.div
                                    initial={{ opacity: 0, y: 4, scale: 0.98, filter: 'blur(2px)' }}
                                    animate={{ opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' }}
                                    exit={{ opacity: 0, y: -2, scale: 0.985, filter: 'blur(3px)' }}
                                    transition={{ duration: 0.38, ease: 'easeOut' }}
                                    className="mb-1 flex items-center gap-3"
                                >
                                    <div className="relative flex h-9 w-9 items-center justify-center rounded-2xl border border-blue-100 bg-[linear-gradient(135deg,rgba(239,246,255,0.95),rgba(219,234,254,0.95))] shadow-sm shadow-blue-100/80">
                                        <motion.div
                                            animate={{ scale: [0.94, 1.08, 0.94], rotate: [0, 8, -8, 0] }}
                                            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                                        >
                                            <Sparkles size={16} className="text-blue-500" />
                                        </motion.div>
                                    </div>
                                    <p className="text-xs font-black uppercase tracking-[0.22em] text-slate-400">
                                        AI 导师正在生成反馈
                                    </p>
                                </motion.div>
                            )}
                        </AnimatePresence>
                        <div
                            style={{ fontFamily: 'Georgia, Cambria, "Times New Roman", Times, serif' }}
                            className="min-h-16 space-y-4 text-[1.16rem] font-semibold leading-[1.88] tracking-[0.01em] text-slate-700 md:space-y-5 md:text-[1.32rem]"
                        >
                            {(feedbackParagraphs.length > 0 ? feedbackParagraphs : ['']).map((paragraph, idx) => {
                                const isLastParagraph = idx === (feedbackParagraphs.length > 0 ? feedbackParagraphs.length - 1 : 0);
                                return (
                                    <p key={`${idx}-${paragraph.slice(0, 24)}`} className="m-0">
                                        {paragraph}
                                        {hasTypingCursor && isLastParagraph && (
                                            <span className="ml-1 inline-block h-6 w-[2px] translate-y-1 animate-pulse bg-slate-400" />
                                        )}
                                    </p>
                                );
                            })}
                        </div>
                        {speechMode && feedback.recognizedText && (
                            <div className="rounded-2xl bg-white/90 px-4 py-3">
                                <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-400">本次识别文本</p>
                                <p className="mt-1 text-base font-semibold text-slate-700">
                                    "{feedback.recognizedText}"
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div className="flex flex-col gap-3">
                {feedback.level === 1 ? (
                    <>
                        <button
                            ref={primaryButtonRef}
                            onClick={onRetry}
                            onFocus={() => setActiveAction('retry')}
                            disabled={retryDisabled}
                            className={`w-full py-5 rounded-[1.2rem] font-black text-xl transition-all flex items-center justify-center gap-3 shadow-lg disabled:bg-slate-200 disabled:text-slate-400 ${resolveButtonClass('retry')}`}
                        >
                            {isBusy ? <Loader2 className="animate-spin" /> : <RefreshCcw size={22} />}
                            {speechMode ? '重新录音' : '重新作答'}
                            <span className={`ml-2 font-normal text-xs uppercase tracking-widest opacity-70 ${enterHintClass('retry')}`}>Enter</span>
                        </button>
                        <button
                            onClick={onSkip}
                            onFocus={() => setActiveAction('skip')}
                            className={`w-full py-5 rounded-[1.2rem] font-black text-xl transition-all flex items-center justify-center gap-3 shadow-lg ${resolveButtonClass('skip')}`}
                        >
                            跳过本题
                            <ArrowRight size={22} />
                        </button>
                    </>
                ) : (
                    <button
                        ref={primaryButtonRef}
                        onClick={onNext}
                        onFocus={() => setActiveAction('next')}
                        className={`w-full py-5 rounded-[1.2rem] font-black text-xl transition-all flex items-center justify-center shadow-lg ${resolveButtonClass('next')}`}
                    >
                        {currentIndex === totalQuestions - 1 ? '完成本轮练习' : '下一题'}
                        <span className={`ml-3 font-normal text-xs uppercase tracking-widest opacity-70 ${enterHintClass('next')}`}>Enter</span>
                    </button>
                )}
            </div>

            <WordContextCard
                word={currentQuestion.original_text}
                pinyin={currentQuestion.original_pinyin}
                metadata={currentQuestion.metadata}
                knowledgeData={knowledgeDetails}
            />
        </motion.div>
    );
}
