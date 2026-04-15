import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Volume2 } from 'lucide-react';
import { claimGlobalAudio, releaseGlobalAudio } from '../utils/audioPlayback';

const API_BASE = import.meta.env.VITE_APP_API_BASE_URL;

// ─────────────────────────────────────────────────────────────────────────────
// AUDIO HELPERS
// ─────────────────────────────────────────────────────────────────────────────

/** Play a pre-recorded pinyin file from R2: zh/audio/pinyin/{filename} */
function playPinyinAudio(filename) {
    if (!filename) return;
    const audio = new Audio(`${API_BASE}/media/pinyin/${encodeURIComponent(filename)}`);
    claimGlobalAudio(audio);
    audio.onpause = () => releaseGlobalAudio(audio);
    audio.onended = () => releaseGlobalAudio(audio);
    audio.onerror = () => releaseGlobalAudio(audio);
    audio.play().catch(() => releaseGlobalAudio(audio));
}

/** Fallback: play arbitrary text via TTS (used for example words in detail pages) */
function playTTS(text) {
    if (!text) return;
    const audio = new Audio(`${API_BASE}/study/tts?text=${encodeURIComponent(text)}`);
    claimGlobalAudio(audio);
    audio.onpause = () => releaseGlobalAudio(audio);
    audio.onended = () => releaseGlobalAudio(audio);
    audio.onerror = () => releaseGlobalAudio(audio);
    audio.play().catch(() => releaseGlobalAudio(audio));
}

// ─────────────────────────────────────────────────────────────────────────────
// DATA
// ─────────────────────────────────────────────────────────────────────────────

// Introduction page: character breakdown examples
// audioFile: filename in zh/audio/pinyin/ on R2
const INTRO_EXAMPLES = [
    { hanzi: '他', initial: 't', final: 'a', toneMark: '¯', syllable: 'tā',  audioFile: 'ta1.wav' },
    { hanzi: '明', initial: 'm', final: 'ing', toneMark: '´', syllable: 'míng', audioFile: 'ming2.wav' },
    { hanzi: '好', initial: 'h', final: 'ao', toneMark: 'ˇ', syllable: 'hǎo', audioFile: 'hao3.wav' },
    { hanzi: '不', initial: 'b', final: 'u', toneMark: '`', syllable: 'bù',  audioFile: 'bu4.wav' },
];

// Initials grid
const INITIALS_GROUPS = [
    ['b', 'p', 'm', 'f'],
    ['d', 't', 'n', 'l'],
    ['g', 'k', 'h'],
    ['j', 'q', 'x'],
    ['zh', 'ch', 'sh', 'r'],
    ['z', 'c', 's'],
];

// Map each initial symbol → audio filename
const INITIAL_AUDIO = {
    b: 'bo1.wav',  p: 'po1.wav',  m: 'mo1.wav',  f: 'fo1.wav',
    d: 'de1.wav',  t: 'te1.wav',  n: 'ne1.wav',  l: 'le1.wav',
    g: 'ge1.wav',  k: 'ke1.wav',  h: 'he1.wav',
    j: 'ji1.wav',  q: 'qi1.wav',  x: 'xi1.wav',
    zh: 'zhi1.wav', ch: 'chi1.wav', sh: 'shi1.wav', r: 'ri1.wav',
    z: 'zi1.wav',  c: 'ci1.wav',  s: 'si1.wav',
};

// Finals grid
const FINALS_GROUPS = [
    ['a', 'ai', 'an', 'ang', 'ao'],
    ['o', 'ou', 'ong', 'iong'],
    ['e', 'ei', 'en', 'eng', 'er'],
    ['i', 'ie', 'in', 'ing', 'iu'],
    ['u', 'ui', 'un', 'uo'],
    ['ü', 'üe', 'ün', 'üan'],
    ['ia', 'ian', 'iang', 'iao'],
    ['ua', 'uai', 'uan', 'uang'],
];

// Map each final display label → audio filename
const FINAL_AUDIO = {
    a: 'a1.wav',   ai: 'ai1.wav',  an: 'an1.wav',   ang: 'ang1.wav',  ao: 'ao1.wav',
    o: 'o1.wav',   ou: 'ou1.wav',  ong: 'ong1.wav',  iong: 'yong1.wav',
    e: 'e1.wav',   ei: 'ei1.wav',  en: 'en1.wav',   eng: 'eng1.wav',  er: 'er1.wav',
    i: 'yi1.wav',  ie: 'ye1.wav',  in: 'yin1.wav',  ing: 'ying1.wav', iu: 'you1.wav',
    u: 'wu1.wav',  ui: 'wei1.wav', un: 'wen1.wav',  uo: 'wo1.wav',
    ü: 'yu1.wav',  üe: 'yue1.wav', ün: 'yun1.wav',  üan: 'yuan1.wav',
    ia: 'ya1.wav', ian: 'yan1.wav', iang: 'yang1.wav', iao: 'yao1.wav',
    ua: 'wa1.wav', uai: 'wai1.wav', uan: 'wan1.wav',  uang: 'wang1.wav',
};

// Tones — mark is the diacritic character shown enlarged; audioFile for pre-recorded demo
const TONES = [
    { number: 1, nameEn: 'high & level',   mark: '¯', pinyin: 'mā', hanzi: '妈', meaning: 'mom',              audioFile: 'ma1.wav' },
    { number: 2, nameEn: 'rising',         mark: '´', pinyin: 'má', hanzi: '麻', meaning: 'hemp',             audioFile: 'ma2.wav' },
    { number: 3, nameEn: 'falling-rising', mark: 'ˇ', pinyin: 'mǎ', hanzi: '马', meaning: 'horse',            audioFile: 'ma3.wav' },
    { number: 4, nameEn: 'falling',        mark: '`', pinyin: 'mà', hanzi: '骂', meaning: 'to scold',         audioFile: 'ma4.wav' },
    { number: 5, nameEn: 'neutral',        mark: '·', pinyin: 'ma', hanzi: '吗', meaning: 'question particle', audioFile: 'ma5.wav' },
];

// ─────────────────────────────────────────────────────────────────────────────
// DETAIL PAGES — one per initial group
// ─────────────────────────────────────────────────────────────────────────────
const DETAIL_PAGES = [
    {
        id: 'b-p-m-f',
        title: 'b  p  m  f',
        subtitle: 'Labial consonants — formed with the lips',
        sounds: [
            {
                symbol: 'b', audioFile: 'bo1.wav',
                description: 'Like "b" in "boy" but unaspirated — no puff of air. Hold your hand in front of your mouth, you should feel almost no breath.',
                examples: [{ hanzi: '笔', pinyin: 'bǐ', meaning: 'pen', audioFile: 'bi3.wav' }, { hanzi: '爸爸', pinyin: 'bàba', meaning: 'dad', audioFile: '爸爸.wav' }],
            },
            {
                symbol: 'p', audioFile: 'po1.wav',
                description: 'Like "p" in "poke" with strong aspiration. You should feel a clear puff of air on your hand.',
                examples: [{ hanzi: '爬', pinyin: 'pá', meaning: 'to climb', audioFile: 'pa2.wav' }, { hanzi: '批评', pinyin: 'pīpíng', meaning: 'to criticise', audioFile: '批评.wav' }],
            },
            {
                symbol: 'm', audioFile: 'mo1.wav',
                description: 'Identical to "m" in "mother". A nasal sound — air flows through the nose.',
                examples: [{ hanzi: '妈妈', pinyin: 'māma', meaning: 'mother', audioFile: '妈妈.wav' }, { hanzi: '猫', pinyin: 'māo', meaning: 'cat', audioFile: 'mao1.wav' }],
            },
            {
                symbol: 'f', audioFile: 'fo1.wav',
                description: 'Identical to "f" in "father". Upper teeth lightly touch the lower lip.',
                examples: [{ hanzi: '法', pinyin: 'fǎ', meaning: 'law', audioFile: 'fa3.wav' }, { hanzi: '犯法', pinyin: 'fànfǎ', meaning: 'break the law', audioFile: '犯法.wav' }],
            },
        ],
    },
    {
        id: 'd-t-n-l',
        title: 'd  t  n  l',
        subtitle: 'Alveolar consonants — tongue tip touches the ridge behind the upper teeth',
        sounds: [
            {
                symbol: 'd', audioFile: 'de1.wav',
                description: 'Like "d" in "dog" but unaspirated — no puff of air.',
                examples: [{ hanzi: '打', pinyin: 'dǎ', meaning: 'to hit', audioFile: 'da3.wav' }, { hanzi: '得到', pinyin: 'dédào', meaning: 'to obtain', audioFile: '得到.wav' }],
            },
            {
                symbol: 't', audioFile: 'te1.wav',
                description: 'Like "t" in "top" with clear aspiration.',
                examples: [{ hanzi: '他', pinyin: 'tā', meaning: 'he / him', audioFile: 'ta1.wav' }, { hanzi: '讨厌', pinyin: 'tǎoyàn', meaning: 'annoying', audioFile: '讨厌.wav' }],
            },
            {
                symbol: 'n', audioFile: 'ne1.wav',
                description: 'Like "n" in "name". A nasal sound — air flows through the nose.',
                examples: [{ hanzi: '你', pinyin: 'nǐ', meaning: 'you', audioFile: 'ni3.wav' }, { hanzi: '难', pinyin: 'nán', meaning: 'difficult', audioFile: 'nan2.wav' }],
            },
            {
                symbol: 'l', audioFile: 'le1.wav',
                description: 'Like "l" in "love". Tongue tip touches the ridge, air flows around the sides.',
                examples: [{ hanzi: '路', pinyin: 'lù', meaning: 'road', audioFile: 'lu4.wav' }, { hanzi: '漂亮', pinyin: 'piàoliang', meaning: 'pretty', audioFile: '漂亮.wav' }],
            },
        ],
    },
    {
        id: 'g-k-h',
        title: 'g  k  h',
        subtitle: 'Velar consonants — back of tongue touches the soft palate',
        sounds: [
            {
                symbol: 'g', audioFile: 'ge1.wav',
                description: 'Like "g" in "go" but unaspirated — no puff of air.',
                examples: [{ hanzi: '高', pinyin: 'gāo', meaning: 'tall', audioFile: 'gao1.wav' }, { hanzi: '哥哥', pinyin: 'gēge', meaning: 'older brother', audioFile: '哥哥.wav' }],
            },
            {
                symbol: 'k', audioFile: 'ke1.wav',
                description: 'Like "k" in "key" with strong aspiration.',
                examples: [{ hanzi: '看', pinyin: 'kàn', meaning: 'to see', audioFile: 'kan4.wav' }, { hanzi: '可以', pinyin: 'kěyǐ', meaning: 'can / may', audioFile: '可以.wav' }],
            },
            {
                symbol: 'h', audioFile: 'he1.wav',
                description: 'Like "h" in "hot" but with more friction — slightly rougher than the English h.',
                examples: [{ hanzi: '好', pinyin: 'hǎo', meaning: 'good', audioFile: 'hao3.wav' }, { hanzi: '喝', pinyin: 'hē', meaning: 'to drink', audioFile: 'he1.wav' }],
            },
        ],
    },
    {
        id: 'j-q-x',
        title: 'j  q  x',
        subtitle: 'Palatal consonants — only combine with i and ü finals',
        sounds: [
            {
                symbol: 'j', audioFile: 'ji1.wav',
                description: 'Sounds kind of like "j" in English "jeep", but with the tip of the tongue behind the lower teeth.',
                examples: [{ hanzi: '家', pinyin: 'jiā', meaning: 'home', audioFile: 'jia1.wav' }, { hanzi: '橘子', pinyin: 'júzi', meaning: 'tangerine', audioFile: '橘子.wav' }],
            },
            {
                symbol: 'q', audioFile: 'qi1.wav',
                description: 'Sounds kind of like "ch" in English "cheap", but with the tip of the tongue behind the lower teeth.',
                examples: [{ hanzi: '钱', pinyin: 'qián', meaning: 'money', audioFile: 'qian2.wav' }, { hanzi: '去', pinyin: 'qù', meaning: 'to go', audioFile: 'qu4.wav' }],
            },
            {
                symbol: 'x', audioFile: 'xi1.wav',
                description: 'Sounds kind of like "sh" in English "sheep", but with the tip of the tongue behind the lower teeth.',
                examples: [{ hanzi: '小', pinyin: 'xiǎo', meaning: 'small', audioFile: 'xiao3.wav' }, { hanzi: '也许', pinyin: 'yěxǔ', meaning: 'perhaps', audioFile: '也许.wav' }],
            },
        ],
    },
    {
        id: 'zh-ch-sh-r',
        title: 'zh  ch  sh  r',
        subtitle: 'Retroflex consonants — tongue tip curls up toward the hard palate',
        sounds: [
            {
                symbol: 'zh', audioFile: 'zhi1.wav',
                description: 'Like "j" in "jar" but with the tongue tip curled back toward the palate. Unaspirated.',
                examples: [{ hanzi: '知道', pinyin: 'zhīdào', meaning: 'to know', audioFile: '知道.wav' }, { hanzi: '照片', pinyin: 'zhàopiàn', meaning: 'photograph', audioFile: '照片.wav' }],
            },
            {
                symbol: 'ch', audioFile: 'chi1.wav',
                description: 'Like "ch" in "chair" but with the tongue tip curled back. Aspirated.',
                examples: [{ hanzi: '吃', pinyin: 'chī', meaning: 'to eat', audioFile: 'chi1.wav' }, { hanzi: '出去', pinyin: 'chūqù', meaning: 'to go out', audioFile: '出去.wav' }],
            },
            {
                symbol: 'sh', audioFile: 'shi1.wav',
                description: 'Like "sh" in "shoe" but with the tongue tip curled back further.',
                examples: [{ hanzi: '十', pinyin: 'shí', meaning: 'ten', audioFile: 'shi2.wav' }, { hanzi: '生活', pinyin: 'shēnghuó', meaning: 'life', audioFile: '生活.wav' }],
            },
            {
                symbol: 'r', audioFile: 'ri1.wav',
                description: 'No direct English equivalent. Start with "r" in "run", curl the tongue back, and add a slight buzz.',
                examples: [{ hanzi: '日', pinyin: 'rì', meaning: 'sun / day', audioFile: 'ri4.wav' }, { hanzi: '人', pinyin: 'rén', meaning: 'person', audioFile: 'ren2.wav' }],
            },
        ],
    },
    {
        id: 'z-c-s',
        title: 'z  c  s',
        subtitle: 'Sibilant consonants — tongue tip near the back of the lower teeth',
        sounds: [
            {
                symbol: 'z', audioFile: 'zi1.wav',
                description: 'Like "ds" in "beds". Tongue tip near lower teeth. Unaspirated.',
                examples: [{ hanzi: '自己', pinyin: 'zìjǐ', meaning: 'oneself', audioFile: '自己.wav' }, { hanzi: '再见', pinyin: 'zàijiàn', meaning: 'goodbye', audioFile: '再见.wav' }],
            },
            {
                symbol: 'c', audioFile: 'ci1.wav',
                description: 'Like "ts" in "cats". The aspirated version of z.',
                examples: [{ hanzi: '词', pinyin: 'cí', meaning: 'word', audioFile: 'ci2.wav' }, { hanzi: '厕所', pinyin: 'cèsuǒ', meaning: 'bathroom', audioFile: '厕所.wav' }],
            },
            {
                symbol: 's', audioFile: 'si1.wav',
                description: 'Like "s" in "sun". Tongue tip near the lower teeth.',
                examples: [{ hanzi: '四', pinyin: 'sì', meaning: 'four', audioFile: 'si4.wav' }, { hanzi: '三', pinyin: 'sān', meaning: 'three', audioFile: 'san1.wav' }],
            },
        ],
    },
];

// ─────────────────────────────────────────────────────────────────────────────
// FINALS DETAIL PAGES — one per finals group, same order as FINALS_GROUPS
// ─────────────────────────────────────────────────────────────────────────────
const FINALS_DETAIL_PAGES = [
    {
        id: 'a-ai-an-ang-ao',
        title: 'a  ai  an  ang  ao',
        subtitle: 'a-family finals — open vowel, mouth wide',
        sounds: [
            {
                symbol: 'a', audioFile: 'a1.wav',
                description: 'Like "a" in "father". Mouth wide open, tongue low and flat.',
                examples: [{ hanzi: '妈', pinyin: 'mā', meaning: 'mom', audioFile: 'ma1.wav' }, { hanzi: '他', pinyin: 'tā', meaning: 'he', audioFile: 'ta1.wav' }],
            },
            {
                symbol: 'ai', audioFile: 'ai1.wav',
                description: 'Like "eye" in English. Start with "a" and glide toward "i".',
                examples: [{ hanzi: '快', pinyin: 'kuài', meaning: 'fast', audioFile: 'kuai4.wav' }, { hanzi: '可爱', pinyin: 'kěài', meaning: 'adorable', audioFile: '可爱.wav' }],
            },
            {
                symbol: 'an', audioFile: 'an1.wav',
                description: 'Like "an" in "ban". End with the tongue touching the roof of the mouth nasally.',
                examples: [{ hanzi: '难', pinyin: 'nán', meaning: 'difficult', audioFile: 'nan2.wav' }, { hanzi: '年', pinyin: 'nián', meaning: 'year', audioFile: 'nian2.wav' }],
            },
            {
                symbol: 'ang', audioFile: 'ang1.wav',
                description: 'Like "ong" in "gong" but with "a". Nasal ending — air flows through the nose.',
                examples: [{ hanzi: '狼', pinyin: 'láng', meaning: 'wolf', audioFile: 'lang2.wav' }, { hanzi: '漂亮', pinyin: 'piàoliang', meaning: 'pretty', audioFile: '漂亮.wav' }],
            },
            {
                symbol: 'ao', audioFile: 'ao1.wav',
                description: 'Like "ow" in "cow". Start with "a" and glide toward "o".',
                examples: [{ hanzi: '到', pinyin: 'dào', meaning: 'to arrive', audioFile: 'dao4.wav' }, { hanzi: '鸟', pinyin: 'niǎo', meaning: 'bird', audioFile: 'niao3.wav' }],
            },
        ],
    },
    {
        id: 'o-ou-ong-iong',
        title: 'o  ou  ong  iong',
        subtitle: 'o-family finals — lips rounded',
        sounds: [
            {
                symbol: 'o', audioFile: 'o1.wav',
                description: 'Like "or" in British English (no r). Lips rounded, mouth slightly open.',
                examples: [{ hanzi: '泼', pinyin: 'pō', meaning: 'to splash', audioFile: 'po1.wav' }, { hanzi: '国', pinyin: 'guó', meaning: 'country', audioFile: 'guo2.wav' }],
            },
            {
                symbol: 'ou', audioFile: 'ou1.wav',
                description: 'Like "oh" in "go". Start with "o" and glide toward "u".',
                examples: [{ hanzi: '头', pinyin: 'tóu', meaning: 'head', audioFile: 'tou2.wav' }, { hanzi: '不够', pinyin: 'búgòu', meaning: 'not enough', audioFile: '不够.wav' }],
            },
            {
                symbol: 'ong', audioFile: 'ong1.wav',
                description: 'Like "ong" in "gong". Lips rounded, nasal ending. Also appears as "iong" after i- (written "yong").',
                examples: [{ hanzi: '用', pinyin: 'yòng', meaning: 'to use' }, { hanzi: '熊', pinyin: 'xióng', meaning: 'bear' }],
            },
        ],
    },
    {
        id: 'e-ei-en-eng-er',
        title: 'e  ei  en  eng  er',
        subtitle: 'e-family finals',
        sounds: [
            {
                symbol: 'e', audioFile: 'e1.wav',
                description: 'A mid-back vowel. Like the "e" in "the" but deeper — tongue pulled back, mouth half open.',
                examples: [{ hanzi: '喝', pinyin: 'hē', meaning: 'to drink', audioFile: 'he1.wav' }, { hanzi: '得到', pinyin: 'dédào', meaning: 'to obtain', audioFile: '得到.wav' }],
            },
            {
                symbol: 'ei', audioFile: 'ei1.wav',
                description: 'Like "ay" in "say". Start with "e" and glide toward "i".',
                examples: [{ hanzi: '给', pinyin: 'gěi', meaning: 'to give', audioFile: 'gei3.wav' }],
            },
            {
                symbol: 'en', audioFile: 'en1.wav',
                description: 'Like "un" in "fun". Nasal ending — tongue tip touches the ridge behind upper teeth.',
                examples: [{ hanzi: '门', pinyin: 'mén', meaning: 'door', audioFile: 'men2.wav' }, { hanzi: '面粉', pinyin: 'miànfěn', meaning: 'flour', audioFile: '面粉.wav' }],
            },
            {
                symbol: 'eng', audioFile: 'eng1.wav',
                description: 'Like "eng" in "length". Back nasal ending — tongue back, air through nose.',
                examples: [{ hanzi: '等', pinyin: 'děng', meaning: 'to wait', audioFile: 'deng3.wav' }, { hanzi: '朋友', pinyin: 'péngyou', meaning: 'friend', audioFile: '朋友.wav' }],
            },
            {
                symbol: 'er', audioFile: 'er1.wav',
                description: 'Like "er" in British "her". The tongue curls back slightly — a retroflex vowel unique to Mandarin.',
                examples: [{ hanzi: '二', pinyin: 'èr', meaning: 'two' }, { hanzi: '耳', pinyin: 'ěr', meaning: 'ear' }],
            },
        ],
    },
    {
        id: 'i-ie-in-ing-iu',
        title: 'i  ie  in  ing  iu',
        subtitle: 'i-family finals — tongue high, lips spread',
        sounds: [
            {
                symbol: 'i', audioFile: 'yi1.wav',
                description: 'Like "ee" in "see". Written as "yi" when there is no initial consonant.',
                examples: [{ hanzi: '一', pinyin: 'yī', meaning: 'one', audioFile: 'yi1.wav' }, { hanzi: '衣服', pinyin: 'yīfu', meaning: 'clothes', audioFile: '衣服.wav' }],
            },
            {
                symbol: 'ie', audioFile: 'ye1.wav',
                description: 'Like "yeah" in English. Written as "ye" when there is no initial consonant.',
                examples: [{ hanzi: '也', pinyin: 'yě', meaning: 'also' }, { hanzi: '别', pinyin: 'bié', meaning: 'don\'t / other' }],
            },
            {
                symbol: 'in', audioFile: 'yin1.wav',
                description: 'Like "een" with a nasal ending. Written as "yin" without an initial.',
                examples: [{ hanzi: '音', pinyin: 'yīn', meaning: 'sound / music', audioFile: 'yin1.wav' }, { hanzi: '新', pinyin: 'xīn', meaning: 'new' }],
            },
            {
                symbol: 'ing', audioFile: 'ying1.wav',
                description: 'Like "ing" in "sing". Written as "ying" without an initial.',
                examples: [{ hanzi: '名', pinyin: 'míng', meaning: 'name', audioFile: 'ming2.wav' }],
            },
            {
                symbol: 'iu', audioFile: 'you1.wav',
                description: 'Combines "i" with "ou". Written as "you" without an initial.',
                examples: [{ hanzi: '六', pinyin: 'liù', meaning: 'six' }],
            },
        ],
    },
    {
        id: 'u-ui-un-uo',
        title: 'u  ui  un  uo',
        subtitle: 'u-family finals — lips rounded and forward',
        sounds: [
            {
                symbol: 'u', audioFile: 'wu1.wav',
                description: 'Like "oo" in "food". Lips rounded and pushed forward. Written as "wu" without an initial.',
                examples: [{ hanzi: '五', pinyin: 'wǔ', meaning: 'five', audioFile: 'wu3.wav' }, { hanzi: '衣服', pinyin: 'yīfu', meaning: 'clothes', audioFile: '衣服.wav' }],
            },
            {
                symbol: 'ui', audioFile: 'wei1.wav',
                description: 'Combines "u" with "ei". Sounds like "way". Written as "wei" without an initial.',
                examples: [{ hanzi: '腿', pinyin: 'tuǐ', meaning: 'leg', audioFile: 'tui3.wav' }, { hanzi: '水', pinyin: 'shuǐ', meaning: 'water' }],
            },
            {
                symbol: 'un', audioFile: 'wen1.wav',
                description: 'Combines "u" with "en". Written as "wen" without an initial.',
                examples: [{ hanzi: '婚姻', pinyin: 'hūnyīn', meaning: 'marriage', audioFile: '婚姻.wav' }],
            },
            {
                symbol: 'uo', audioFile: 'wo1.wav',
                description: 'Combines "u" with "o". Written as "wo" without an initial.',
                examples: [{ hanzi: '国', pinyin: 'guó', meaning: 'country', audioFile: 'guo2.wav' }],
            },
        ],
    },
    {
        id: 'ü-üe-ün-üan',
        title: 'ü  üe  ün  üan',
        subtitle: 'ü-family finals — like French "u", lips rounded while saying "ee"',
        note: 'Spelling rule: ü loses its two dots after j, q, x, and y — it is written simply as u. So jū, qū, xū are all ü; and yu, yue, yun, yuan all contain ü underneath.',
        sounds: [
            {
                symbol: 'ü', audioFile: 'yu1.wav',
                description: 'No equivalent in English. Round your lips as if saying "oo", then say "ee". After j / q / x the dots are dropped and written as u. Standalone: written as yu.',
                examples: [{ hanzi: '女', pinyin: 'nǚ', meaning: 'female / woman' }, { hanzi: '法律', pinyin: 'fǎlǜ', meaning: 'law' }],
            },
            {
                symbol: 'üe', audioFile: 'yue1.wav',
                description: 'Combines "ü" with "e". After j / q / x written as ue; standalone written as yue. So 音乐 yīnyuè is typed "yinyue".',
                examples: [{ hanzi: '月', pinyin: 'yuè', meaning: 'moon / month' }, { hanzi: '音乐', pinyin: 'yīnyuè', meaning: 'music' }],
            },
            {
                symbol: 'ün', audioFile: 'yun1.wav',
                description: 'Combines "ü" with "n". After j / q / x written as un; standalone written as yun.',
                examples: [{ hanzi: '云', pinyin: 'yún', meaning: 'cloud' }, { hanzi: '军', pinyin: 'jūn', meaning: 'army / military' }],
            },
            {
                symbol: 'üan', audioFile: 'yuan1.wav',
                description: 'Combines "ü" with "an". After j / q / x written as uan; standalone written as yuan.',
                examples: [{ hanzi: '远', pinyin: 'yuǎn', meaning: 'far' }, { hanzi: '圆', pinyin: 'yuán', meaning: 'round / circle' }],
            },
        ],
    },
    {
        id: 'ia-ian-iang-iao',
        title: 'ia  ian  iang  iao',
        subtitle: 'ia-family finals — i + a-vowel combinations',
        sounds: [
            {
                symbol: 'ia', audioFile: 'ya1.wav',
                description: 'Combines "i" with "a". Written as "ya" without an initial.',
                examples: [{ hanzi: '家', pinyin: 'jiā', meaning: 'home', audioFile: 'jia1.wav' }, { hanzi: '牙', pinyin: 'yá', meaning: 'tooth', audioFile: 'ya2.wav' }],
            },
            {
                symbol: 'ian', audioFile: 'yan1.wav',
                description: 'Combines "i" with "an". Written as "yan" without an initial.',
                examples: [{ hanzi: '钱', pinyin: 'qián', meaning: 'money', audioFile: 'qian2.wav' }, { hanzi: '年', pinyin: 'nián', meaning: 'year', audioFile: 'nian2.wav' }],
            },
            {
                symbol: 'iang', audioFile: 'yang1.wav',
                description: 'Combines "i" with "ang". Written as "yang" without an initial.',
                examples: [{ hanzi: '漂亮', pinyin: 'piàoliang', meaning: 'pretty', audioFile: '漂亮.wav' }, { hanzi: '想', pinyin: 'xiǎng', meaning: 'to think / want' }],
            },
            {
                symbol: 'iao', audioFile: 'yao1.wav',
                description: 'Combines "i" with "ao". Written as "yao" without an initial.',
                examples: [{ hanzi: '鸟', pinyin: 'niǎo', meaning: 'bird', audioFile: 'niao3.wav' }, { hanzi: '小', pinyin: 'xiǎo', meaning: 'small', audioFile: 'xiao3.wav' }],
            },
        ],
    },
    {
        id: 'ua-uai-uan-uang',
        title: 'ua  uai  uan  uang',
        subtitle: 'ua-family finals — u + a-vowel combinations',
        sounds: [
            {
                symbol: 'ua', audioFile: 'wa1.wav',
                description: 'Combines "u" with "a". Written as "wa" without an initial.',
                examples: [{ hanzi: '花', pinyin: 'huā', meaning: 'flower' }, { hanzi: '瓜', pinyin: 'guā', meaning: 'melon' }],
            },
            {
                symbol: 'uai', audioFile: 'wai1.wav',
                description: 'Combines "u" with "ai". Written as "wai" without an initial.',
                examples: [{ hanzi: '快', pinyin: 'kuài', meaning: 'fast', audioFile: 'kuai4.wav' }],
            },
            {
                symbol: 'uan', audioFile: 'wan1.wav',
                description: 'Combines "u" with "an". Written as "wan" without an initial.',
                examples: [{ hanzi: '远', pinyin: 'yuǎn', meaning: 'far' }, { hanzi: '暖', pinyin: 'nuǎn', meaning: 'warm' }],
            },
            {
                symbol: 'uang', audioFile: 'wang1.wav',
                description: 'Combines "u" with "ang". Written as "wang" without an initial.',
                examples: [{ hanzi: '双', pinyin: 'shuāng', meaning: 'pair / double' }, { hanzi: '黄', pinyin: 'huáng', meaning: 'yellow' }],
            },
        ],
    },
];

// Combined: initials first, then finals
const ALL_PAGES = [...DETAIL_PAGES, ...FINALS_DETAIL_PAGES];

// ─────────────────────────────────────────────────────────────────────────────
// SHARED COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

function AudioButton({ audioFile, size = 'md' }) {
    const sz = size === 'sm' ? 14 : 18;
    return (
        <button
            onClick={() => playPinyinAudio(audioFile)}
            className="inline-flex items-center justify-center text-slate-400 hover:text-blue-500 transition-colors"
            aria-label={`Play ${audioFile}`}
        >
            <Volume2 size={sz} />
        </button>
    );
}

function SoundButton({ label, audioFile }) {
    return (
        <button
            onClick={() => playPinyinAudio(audioFile)}
            className="px-4 py-2.5 border border-slate-200 rounded-xl text-base font-mono font-semibold text-slate-700
                       hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50 active:scale-95
                       transition-all min-w-[52px] text-center"
        >
            {label}
        </button>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// INTRO PAGE
// ─────────────────────────────────────────────────────────────────────────────
function IntroPage({ onGroupClick }) {
    return (
        <div className="space-y-10">
            {/* Character breakdown examples */}
            <section>
                <h2 className="text-3xl font-black text-slate-900 mb-2">Introduction</h2>
                <p className="text-slate-500 text-base mb-6">
                    Chinese syllables have three parts: an <strong>initial</strong>, a <strong>final</strong>, and a <strong>tone</strong>.
                </p>
                <div className="rounded-2xl border border-slate-100 overflow-hidden shadow-sm">
                    <div className="grid grid-cols-[3rem_1fr_1fr_1fr_1fr_2.5rem] gap-x-4 px-6 py-3 bg-slate-50 border-b border-slate-100">
                        {['', 'Initial', 'Final', 'Tone', 'Syllable', ''].map((h, i) => (
                            <span key={i} className="text-xs font-bold text-slate-400 uppercase tracking-wide">{h}</span>
                        ))}
                    </div>
                    {INTRO_EXAMPLES.map((ex) => (
                        <div key={ex.hanzi} className="grid grid-cols-[3rem_1fr_1fr_1fr_1fr_2.5rem] gap-x-4 items-center px-6 py-4 border-b last:border-0 border-slate-50 hover:bg-slate-50/50">
                            <span className="text-3xl font-bold text-slate-800">{ex.hanzi}</span>
                            <span className="font-mono text-lg text-slate-600">{ex.initial}</span>
                            <span className="font-mono text-lg text-slate-600">{ex.final}</span>
                            <span className="font-mono text-slate-500 text-3xl">{ex.toneMark}</span>
                            <span className="font-mono text-lg font-semibold text-blue-600">{ex.syllable}</span>
                            <AudioButton audioFile={ex.audioFile} />
                        </div>
                    ))}
                </div>
            </section>

            {/* Initials + Finals side by side */}
            <div className="grid grid-cols-2 gap-x-10">
                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-2">Initials</h2>
                    <p className="text-sm text-slate-400 mb-4 flex items-center gap-1"><Volume2 size={14} /> Tap to listen · click group to explore</p>
                    <div className="space-y-2">
                        {INITIALS_GROUPS.map((row, ri) => {
                            const pageId = ALL_PAGES.find(p => p.sounds.some(s => s.symbol === row[0]))?.id;
                            return (
                                <div key={ri} className="flex items-center gap-2">
                                    <div className="flex gap-2 flex-wrap flex-1">
                                        {row.map(sym => <SoundButton key={sym} label={sym} audioFile={INITIAL_AUDIO[sym]} />)}
                                    </div>
                                    {pageId && (
                                        <button onClick={() => onGroupClick(pageId)} className="shrink-0 flex items-center gap-0.5 text-xs font-semibold text-slate-400 hover:text-blue-600 hover:bg-blue-50 px-2 py-1 rounded-lg border border-slate-200 hover:border-blue-200 transition-all">
                                            Detail <ChevronRight size={12} />
                                        </button>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </section>

                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-2">Finals</h2>
                    <p className="text-sm text-slate-400 mb-4 flex items-center gap-1"><Volume2 size={14} /> Tap to listen · click group to explore</p>
                    <div className="space-y-2">
                        {FINALS_GROUPS.map((row, ri) => {
                            const pageId = ALL_PAGES.find(p => p.sounds.some(s => s.symbol === row[0]))?.id;
                            return (
                                <div key={ri} className="flex items-center gap-2">
                                    <div className="flex gap-2 flex-wrap flex-1">
                                        {row.map(sym => <SoundButton key={sym} label={sym} audioFile={FINAL_AUDIO[sym]} />)}
                                    </div>
                                    {pageId && (
                                        <button onClick={() => onGroupClick(pageId)} className="shrink-0 flex items-center gap-0.5 text-xs font-semibold text-slate-400 hover:text-blue-600 hover:bg-blue-50 px-2 py-1 rounded-lg border border-slate-200 hover:border-blue-200 transition-all">
                                            Detail <ChevronRight size={12} />
                                        </button>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </section>
            </div>

            {/* Tones */}
            <section>
                <h2 className="text-2xl font-black text-slate-900 mb-2">Tones</h2>
                <p className="text-slate-500 text-sm mb-4">
                    Chinese is a tonal language — the same syllable in different tones means completely different things.
                </p>
                <div className="space-y-3">
                    {TONES.map((t) => (
                        <div key={t.number} className="flex items-center gap-5 bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 hover:border-blue-100 transition-colors">
                            <div className="w-10 shrink-0 text-center">
                                <span className="text-5xl font-bold text-blue-500 leading-none select-none">{t.mark}</span>
                            </div>
                            <div className="flex items-center gap-3 w-28 shrink-0">
                                <span className="text-4xl font-bold text-slate-800 leading-none">{t.hanzi}</span>
                                <span className="font-mono text-lg font-semibold text-blue-600">{t.pinyin}</span>
                            </div>
                            <AudioButton audioFile={t.audioFile} />
                            <div className="flex-1 min-w-0">
                                <div className="text-sm font-semibold text-slate-600">{t.nameEn}</div>
                                <div className="text-sm text-slate-400">{t.meaning}</div>
                            </div>
                            <div className="shrink-0 w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center">
                                <span className="text-xs font-bold text-slate-400">{t.number}</span>
                            </div>
                        </div>
                    ))}
                </div>
                <p className="text-xs text-slate-400 mt-3">The neutral tone (5) is short and unstressed — the tone mark is usually omitted in writing.</p>
            </section>
        </div>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// DETAIL PAGE (one per initial group)
// ─────────────────────────────────────────────────────────────────────────────
function DetailSection({ page, onBackToTop }) {
    return (
        <div className="space-y-6">
            <div className="flex items-start justify-between">
                <div>
                    <h2 className="text-3xl font-black text-slate-900 font-mono tracking-widest mb-1">{page.title}</h2>
                    <p className="text-slate-500">{page.subtitle}</p>
                </div>
                <button onClick={onBackToTop} className="mt-1 shrink-0 text-xs text-slate-400 hover:text-blue-500 flex items-center gap-1 transition-colors">
                    <ChevronLeft size={12} /> Overview
                </button>
            </div>

            {page.note && (
                <div className="flex gap-3 bg-blue-50 border border-blue-100 rounded-2xl px-5 py-4">
                    <span className="text-blue-400 text-lg leading-snug shrink-0">ℹ</span>
                    <p className="text-sm text-blue-700 leading-relaxed">{page.note}</p>
                </div>
            )}

            <div className="space-y-6">
                {page.sounds.map((sound) => (
                    <div key={sound.symbol} className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                        <div className="flex items-center gap-4 mb-3">
                            <button
                                onClick={() => playPinyinAudio(sound.audioFile)}
                                className="w-14 h-14 rounded-xl bg-blue-50 hover:bg-blue-100 border-2 border-blue-100 hover:border-blue-300 flex items-center justify-center font-mono text-2xl font-black text-blue-600 transition-all active:scale-95 shadow-sm"
                            >
                                {sound.symbol}
                            </button>
                            <div>
                                <div className="flex items-center gap-2">
                                    <span className="font-mono text-lg font-bold text-slate-700">{sound.audioFile.replace('.wav', '')}</span>
                                    <AudioButton audioFile={sound.audioFile} size="sm" />
                                </div>
                                <p className="text-sm text-slate-500 mt-0.5">{sound.description}</p>
                            </div>
                        </div>
                        {sound.examples?.length > 0 && (
                            <div className="flex gap-3 flex-wrap mt-3 pt-3 border-t border-slate-50">
                                {sound.examples.map((ex) => (
                                    <button
                                        key={ex.hanzi}
                                        onClick={() => ex.audioFile ? playPinyinAudio(ex.audioFile) : playTTS(ex.hanzi)}
                                        className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-50 hover:bg-blue-50 border border-slate-100 hover:border-blue-200 transition-all group"
                                    >
                                        <span className="text-xl font-bold text-slate-800">{ex.hanzi}</span>
                                        <div className="text-left">
                                            <div className="font-mono text-xs text-blue-500">{ex.pinyin}</div>
                                            <div className="text-xs text-slate-400">{ex.meaning}</div>
                                        </div>
                                        <Volume2 size={12} className="text-slate-300 group-hover:text-blue-400 ml-1" />
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// PROGRESS BAR
// ─────────────────────────────────────────────────────────────────────────────
// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────
export default function PinyinPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const fromPath = location.state?.from || null;
    const [activeSection, setActiveSection] = useState('intro');
    const introRef = useRef(null);

    // Scroll to a section, offset for sticky bars (navbar 64px + sticky bar ~52px)
    const scrollToSection = useCallback((id) => {
        const el = id === 'intro' ? introRef.current : document.getElementById(id);
        if (!el) return;
        const top = el.getBoundingClientRect().top + window.scrollY - 128;
        window.scrollTo({ top, behavior: 'smooth' });
    }, []);

    // Track active section via IntersectionObserver
    useEffect(() => {
        const sections = document.querySelectorAll('[data-section-id]');
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) setActiveSection(entry.target.dataset.sectionId);
                });
            },
            { rootMargin: '-15% 0px -75% 0px', threshold: 0 }
        );
        sections.forEach(s => observer.observe(s));
        return () => observer.disconnect();
    }, []);

    const activePage = ALL_PAGES.find(p => p.id === activeSection);

    return (
        <div className="min-h-screen bg-slate-50 pt-16">
            {/* Back to Lesson floating capsule */}
            {fromPath && (
                <button
                    onClick={() => navigate(fromPath)}
                    className="fixed bottom-6 left-6 z-50 flex items-center gap-2 rounded-full bg-white px-5 py-3 text-base font-semibold text-slate-700 shadow-lg ring-1 ring-slate-200 transition hover:bg-slate-50 hover:shadow-xl hover:ring-blue-300 active:scale-95"
                >
                    <ChevronLeft size={18} />
                    <span>Back to Lesson</span>
                </button>
            )}

            {/* Single scroll content */}
            <div className="max-w-4xl mx-auto px-5 py-8 space-y-20">
                {/* Overview */}
                <div ref={introRef} data-section-id="intro">
                    <IntroPage onGroupClick={scrollToSection} />
                </div>

                {/* All detail sections */}
                {ALL_PAGES.map((page) => (
                    <div
                        key={page.id}
                        id={page.id}
                        data-section-id={page.id}
                        className="scroll-mt-32 border-t border-slate-100 pt-12"
                    >
                        <DetailSection page={page} onBackToTop={() => scrollToSection('intro')} />
                    </div>
                ))}
            </div>
        </div>
    );
}
