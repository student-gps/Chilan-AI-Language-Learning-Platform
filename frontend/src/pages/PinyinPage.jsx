import { useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChevronLeft, ChevronRight, Volume2 } from 'lucide-react';
import { claimGlobalAudio, releaseGlobalAudio } from '../utils/audioPlayback';
import IntroFloatingNav from './introNavigation';

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

const normalizeUiLang = (language) => {
    const code = (language || 'en').split('-')[0].toLowerCase();
    return code === 'ja' ? 'jp' : code;
};

const ARTICULATION_EN = {
    b: 'Close both lips, build pressure, then release gently. This sound is unaspirated, so there should be almost no puff of air.',
    p: 'Close both lips, build pressure, then release with a strong puff of air.',
    m: 'Close both lips and let the voice pass through the nose.',
    f: 'Lightly touch the upper teeth to the lower lip and let air pass through the narrow gap.',
    d: 'Touch the tongue tip to the ridge behind the upper teeth, then release gently. This sound is unaspirated.',
    t: 'Touch the tongue tip to the ridge behind the upper teeth, then release with a clear puff of air.',
    n: 'Touch the tongue tip to the ridge behind the upper teeth and let air flow through the nose.',
    l: 'Touch the tongue tip to the ridge behind the upper teeth and let air flow around the sides of the tongue.',
    g: 'Raise the back of the tongue to the soft palate, build pressure, then release gently. This sound is unaspirated.',
    k: 'Raise the back of the tongue to the soft palate, then release with a strong puff of air.',
    h: 'Raise the back of the tongue close to the soft palate and let air pass through with friction.',
    j: 'Place the tongue tip behind the lower teeth and raise the front of the tongue toward the hard palate. This sound is unaspirated.',
    q: 'Place the tongue tip behind the lower teeth and raise the front of the tongue toward the hard palate, then release with aspiration.',
    x: 'Place the tongue tip behind the lower teeth and let air pass over the front of the tongue with friction.',
    zh: 'Curl the tongue tip back toward the hard palate, build pressure, then release gently. This sound is unaspirated.',
    ch: 'Curl the tongue tip back toward the hard palate, then release with a clear puff of air.',
    sh: 'Curl the tongue tip back and let air pass through with friction.',
    r: 'Curl the tongue tip back and add voice with a light buzzing friction.',
    z: 'Keep the tongue tip near the back of the lower teeth, build pressure, then release gently. This sound is unaspirated.',
    c: 'Keep the tongue tip near the back of the lower teeth, then release with a strong puff of air.',
    s: 'Keep the tongue tip near the back of the lower teeth and let air pass through with friction.',
    a: 'Open the mouth wide. Keep the tongue low and flat.',
    ai: 'Start with an open a sound, then glide toward i.',
    an: 'Start with a, then end with the tongue tip touching the ridge behind the upper teeth while air flows through the nose.',
    ang: 'Start with a, then finish with the back of the tongue raised for a back nasal ending.',
    ao: 'Start with a, then glide toward a rounded o sound.',
    o: 'Round the lips and keep the mouth slightly open.',
    ou: 'Start with rounded o, then glide toward u.',
    ong: 'Round the lips and finish with a back nasal ending.',
    e: 'Use a mid-back vowel: pull the tongue slightly back and keep the mouth half open.',
    ei: 'Start with e, then glide toward i.',
    en: 'Start with e, then end with the tongue tip touching the ridge behind the upper teeth while air flows through the nose.',
    eng: 'Start with e, then finish with a back nasal ending.',
    er: 'Start with e and curl the tongue slightly back.',
    i: 'Keep the tongue high and the lips spread.',
    ie: 'Start with i, then glide toward e.',
    in: 'Start with i, then end with a front nasal n.',
    ing: 'Start with i, then finish with a back nasal ng.',
    iu: 'Start with i, then glide toward ou.',
    u: 'Round the lips and push them forward; keep the tongue high and back.',
    ui: 'Start with u, then glide toward ei.',
    un: 'Start with u, then glide into en.',
    uo: 'Start with u, then glide toward o.',
    'ü': 'Round the lips as for u, but keep the tongue high and forward as for i.',
    'üe': 'Start with ü, then glide toward e.',
    'ün': 'Start with ü, then end with a front nasal n.',
    'üan': 'Start with ü, then glide into an.',
    ia: 'Start with i, then glide toward a.',
    ian: 'Start with i, then glide into an.',
    iang: 'Start with i, then glide into ang.',
    iao: 'Start with i, then glide into ao.',
    ua: 'Start with u, then glide toward a.',
    uai: 'Start with u, then glide into ai.',
    uan: 'Start with u, then glide into an.',
    uang: 'Start with u, then glide into ang.',
};

const GUIDE_TRANSLATIONS = {
    zh: (s) => `发 ${s} 时，请按上方发音动作练习：注意舌位、嘴唇形状、鼻音收尾，以及是否送气。`,
    jp: (s) => `${s} は、舌の位置・唇の形・鼻音の終わり方・息の強さに注意して発音します。`,
    fr: (s) => `Pour ${s}, concentrez-vous sur la position de la langue, la forme des lèvres, la finale nasale et l'aspiration.`,
    de: (s) => `Achte bei ${s} auf Zungenposition, Lippenform, nasalen Ausklang und Behauchung.`,
    ko: (s) => `${s}는 혀 위치, 입술 모양, 비음 끝소리, 그리고 숨의 세기를 기준으로 연습하세요.`,
    es: (s) => `Para ${s}, fíjate en la posición de la lengua, la forma de los labios, el final nasal y la aspiración.`,
    vi: (s) => `Với ${s}, hãy chú ý vị trí lưỡi, hình dạng môi, âm mũi ở cuối và luồng hơi bật ra.`,
    pt: (s) => `Para ${s}, observe a posição da língua, o formato dos lábios, o final nasal e a aspiração.`,
    ar: (s) => `عند نطق ${s}، ركّز على موضع اللسان، شكل الشفتين، النهاية الأنفية، وقوة الهواء.`,
    th: (s) => `สำหรับ ${s} ให้สังเกตตำแหน่งลิ้น รูปปาก เสียงนาสิกท้ายเสียง และแรงลม`,
    ru: (s) => `Для ${s} следите за положением языка, формой губ, носовым окончанием и придыханием.`,
    id: (s) => `Untuk ${s}, perhatikan posisi lidah, bentuk bibir, akhir nasal, dan hembusan udara.`,
    ms: (s) => `Untuk ${s}, perhatikan kedudukan lidah, bentuk bibir, akhiran nasal dan hembusan udara.`,
    it: (s) => `Per ${s}, osserva posizione della lingua, forma delle labbra, finale nasale e aspirazione.`,
};

const NATIVE_HINTS = {
    b: {
        en: 'Similar to "b" in "boy", but with almost no puff of air.',
        fr: 'Plus proche du p français de "papa" que du b français : les lèvres se ferment, sans souffle net.',
        de: 'Eher wie ein unbehauchtes p als ein deutsches b: Lippen schließen, kaum Luftstoß.',
        es: 'Más cercano a una p española suave que a b/v: cierra los labios y suelta sin soplo fuerte.',
        pt: 'Mais próximo de um p sem sopro forte do que de b/v: feche os lábios e solte suavemente.',
        it: 'Più vicino a una p italiana senza soffio forte che a b: labbra chiuse, rilascio morbido.',
        ru: 'Ближе к русскому п без сильного выдоха, а не к звонкому б.',
    },
    p: {
        en: 'Similar to "p" in "poke", with strong aspiration.',
        fr: 'Comme p dans "papa", mais avec un souffle beaucoup plus net après le p.',
        de: 'Wie p in "Park", aber der Luftstoß muss deutlich spürbar sein.',
        es: 'Como p, pero con una bocanada de aire mucho más clara que en español.',
        pt: 'Como p, mas com uma saída de ar bem mais forte que em português.',
        it: 'Come p, ma con un soffio d’aria più forte che in italiano.',
        ru: 'Как п, но с заметным придыханием после смычки.',
    },
    m: {
        en: 'Same basic sound as "m" in "mother".',
        jp: '日本語の「ま」の m にかなり近い音です。',
        fr: 'Comme m dans "maman".',
        de: 'Wie m in "Mama".',
        ko: '한국어 ㅁ과 거의 같습니다.',
        es: 'Como m en "mamá".',
        vi: 'Gần như m trong tiếng Việt.',
        pt: 'Como m em "mamãe".',
        ar: 'قريب من صوت م العربي.',
        th: 'ใกล้กับเสียง ม ในภาษาไทย',
        ru: 'Как м в русском.',
        id: 'Seperti m dalam bahasa Indonesia.',
        ms: 'Seperti m dalam bahasa Melayu.',
        it: 'Come m in "mamma".',
    },
    f: {
        en: 'Same basic sound as "f" in "father".',
        fr: 'Comme f dans "famille".',
        de: 'Wie f in "Familie".',
        ko: '한국어에는 완전히 같은 기본 자음은 드뭅니다. 윗니와 아랫입술 사이로 바람을 내세요.',
        es: 'Como f en "familia".',
        vi: 'Gần với f/ph trong các cách đọc có ma sát môi-răng.',
        pt: 'Como f em "família".',
        ar: 'قريب من صوت ف العربي.',
        th: 'ใกล้กับเสียง ฟ',
        ru: 'Как ф в русском.',
        id: 'Seperti f dalam bahasa Indonesia.',
        ms: 'Seperti f dalam bahasa Melayu.',
        it: 'Come f in "famiglia".',
    },
    d: {
        en: 'Similar to "d" in "dog", but with almost no puff of air.',
        fr: 'Plus proche du t français de "tout" sans souffle que du d français.',
        de: 'Eher wie ein unbehauchtes t als ein deutsches d: Zungenspitze vorne, kaum Luftstoß.',
        es: 'Más cercano a una t española suave que a d: sin soplo fuerte.',
        pt: 'Mais próximo de t sem sopro forte do que de d.',
        it: 'Più vicino a una t italiana senza soffio forte che a d.',
        ru: 'Ближе к русскому т без сильного выдоха, а не к звонкому д.',
    },
    t: {
        en: 'Similar to "t" in "top", with clear aspiration.',
        fr: 'Comme t, mais avec un souffle beaucoup plus clair qu’en français.',
        de: 'Wie t in "Tag", mit deutlich spürbarem Luftstoß.',
        es: 'Como t, pero con mucho más aire que en español.',
        pt: 'Como t, mas com uma saída de ar mais forte que em português.',
        it: 'Come t, ma con un soffio più evidente che in italiano.',
        ru: 'Как т, но с заметным придыханием.',
    },
    n: {
        en: 'Same basic sound as "n" in "name".',
        jp: '日本語の「な」の n に近いですが、舌先を前にしっかり置きます。',
        fr: 'Comme n dans "non".',
        de: 'Wie n in "Name".',
        ko: '한국어 ㄴ과 거의 같습니다.',
        es: 'Como n en "no".',
        vi: 'Gần như n trong tiếng Việt.',
        pt: 'Como n em "não", mas sem nasalizar a vogal inteira.',
        ar: 'قريب من صوت ن العربي.',
        th: 'ใกล้กับเสียง น',
        ru: 'Как н в русском.',
        id: 'Seperti n dalam bahasa Indonesia.',
        ms: 'Seperti n dalam bahasa Melayu.',
        it: 'Come n in "no".',
    },
    l: {
        en: 'Same basic sound as "l" in "love".',
        jp: '日本語のラ行より舌先を前に置き、英語の l に近く出します。',
        fr: 'Comme l dans "lire".',
        de: 'Wie l in "Liebe".',
        ko: '한국어 ㄹ보다 더 분명한 l 소리에 가깝습니다.',
        es: 'Como l en "luna".',
        vi: 'Gần như l trong tiếng Việt.',
        pt: 'Como l em "lua".',
        ar: 'قريب من صوت ل العربي.',
        th: 'ใกล้กับเสียง ล',
        ru: 'Как л, но обычно светлее и переднее.',
        id: 'Seperti l dalam bahasa Indonesia.',
        ms: 'Seperti l dalam bahasa Melayu.',
        it: 'Come l in "luna".',
    },
    g: {
        en: 'Similar to "g" in "go", but unaspirated.',
        fr: 'Plus proche du k français de "kiwi" sans souffle que du g français.',
        de: 'Eher wie ein unbehauchtes k als ein deutsches g: hinten am Gaumen, kaum Luftstoß.',
        es: 'Más cercano a una k española suave que a g: sin soplo fuerte.',
        pt: 'Mais próximo de k sem sopro forte do que de g.',
        it: 'Più vicino a una c/k italiana senza soffio forte che a g.',
        ru: 'Ближе к русскому к без сильного выдоха, а не к звонкому г.',
    },
    k: {
        en: 'Similar to "k" in "key", with strong aspiration.',
        fr: 'Comme k dans "kilo", mais avec un souffle plus net.',
        de: 'Ähnlich wie k in "Kilo", mit deutlicher Behauchung.',
        es: 'Como k/c fuerte, pero con más aire que en español.',
        pt: 'Como c/k forte, mas com mais ar que em português.',
        it: 'Come c/k duro, ma con un soffio più chiaro che in italiano.',
        ru: 'Как к, но с заметным придыханием.',
    },
    h: {
        en: 'Similar to "h" in "hot", but rougher.',
        jp: '日本語の「は」より喉の奥でこすれる音です。',
        fr: 'Pas le h muet français : faites une friction au fond de la bouche, proche d’un j espagnol léger.',
        de: 'Etwas wie ch in "Bach", aber leichter.',
        es: 'Parecido a j en "jamón", pero más ligero.',
        pt: 'Lembra o r forte de alguns sotaques do português, mas mais leve.',
        ru: 'Похоже на х, но мягче и менее напряжённо.',
    },
    j: {
        en: 'A bit like "j" in "jeep", but keep the tongue tip behind the lower teeth.',
        jp: '日本語の「じ」に少し近いですが、舌先は下の歯の裏に置きます。',
        ko: '한국어 ㅈ과 비슷하지만 혀끝은 아랫니 뒤에 두고 더 앞쪽에서 냅니다.',
        ru: 'Отдалённо похоже на мягкое дзь/джь, но язык держите за нижними зубами.',
    },
    q: {
        en: 'A bit like "ch" in "cheap", but more fronted and aspirated.',
        jp: '日本語の「ち」に少し近いですが、もっと前で、息を強く出します。',
        ko: '한국어 ㅊ과 비슷하지만 혀끝은 아랫니 뒤에 두고 더 앞쪽에서 냅니다.',
        ru: 'Отдалённо похоже на мягкое ч, но с более передним положением языка и придыханием.',
    },
    x: {
        en: 'A bit like "sh" in "sheep", but more fronted.',
        jp: '日本語の「し」に近いですが、舌先は下の歯の裏、音はさらに前寄りです。',
        ko: '한국어 ㅅ/시와 비슷하게 들릴 수 있지만 혀끝은 아랫니 뒤에 둡니다.',
        ru: 'Отдалённо похоже на мягкое сь/щ, но язык должен быть за нижними зубами.',
    },
    zh: {
        en: 'A bit like "j" in "jar", but with the tongue curled back.',
        ru: 'Похоже на твёрдое дж/чж, но кончик языка загнут назад.',
    },
    ch: {
        en: 'A bit like "ch" in "chair", but with the tongue curled back and a clear puff of air.',
        ru: 'Похоже на ч, но кончик языка загнут назад и есть придыхание.',
    },
    sh: {
        en: 'Similar to "sh" in "shoe", but curl the tongue tip farther back.',
        fr: 'Proche de ch dans "chat", mais avec la pointe de la langue plus recourbée vers l’arrière.',
        de: 'Ähnlich wie sch in "Schule", aber die Zungenspitze ist weiter zurückgebogen.',
        es: 'Parecido a sh, pero con la punta de la lengua más hacia atrás.',
        pt: 'Parecido com x/ch de alguns sotaques, mas com a ponta da língua mais para trás.',
        ru: 'Очень близко к русскому ш: широкий, твёрдый звук с языком назад.',
    },
    r: {
        en: 'No direct English equivalent. Curl the tongue back and add a light buzz.',
        fr: 'Ce n’est pas le r français : la pointe de la langue se recourbe vers l’arrière avec une légère vibration/friction.',
        de: 'Nicht wie deutsches r: Zungenspitze zurückrollen und leicht stimmhaft reiben.',
        es: 'No es la r española: curva la punta de la lengua hacia atrás y añade una fricción sonora ligera.',
        ru: 'Не русский р: язык загнут назад, без дрожания, с лёгкой звонкой фрикцией.',
    },
    z: {
        en: 'Similar to "ds" in "beds", but unaspirated.',
        de: 'Etwa wie deutsches z in "Zeit", aber ohne starken Luftstoß.',
        ru: 'Похоже на ц, но без заметного придыхания.',
    },
    c: {
        en: 'Similar to "ts" in "cats", with strong aspiration.',
        de: 'Wie deutsches z in "Zeit", aber mit stärkerem Luftstoß.',
        ru: 'Похоже на ц, но с заметным придыханием.',
    },
    s: {
        en: 'Same basic sound as "s" in "sun".',
        jp: '日本語の「す」の s に近いですが、舌先は下の歯の近くです。',
        fr: 'Comme s dans "soleil".',
        de: 'Wie stimmloses s/ß, zum Beispiel in "Straße".',
        ko: '한국어 ㅅ과 비슷하지만 혀끝은 아랫니 가까이에 둡니다.',
        es: 'Como s en "sol".',
        vi: 'Gần với s trong tiếng Việt chuẩn, đặt đầu lưỡi gần răng dưới.',
        pt: 'Como s em "sol".',
        ar: 'قريب من صوت س العربي.',
        th: 'ใกล้กับเสียง ส/ซ',
        ru: 'Как с в русском.',
        id: 'Seperti s dalam bahasa Indonesia.',
        ms: 'Seperti s dalam bahasa Melayu.',
        it: 'Come s sorda in "sole".',
    },
    a: {
        en: 'Similar to "a" in "father".',
        jp: '日本語の「あ」に近く、口をしっかり開けます。',
        fr: 'Proche du a dans "papa".',
        de: 'Ähnlich wie a in "Vater".',
        ko: '한국어 ㅏ와 가깝습니다.',
        es: 'Como a en "casa".',
        vi: 'Gần với a trong tiếng Việt.',
        pt: 'Como a aberto em "casa".',
        ru: 'Как а в русском.',
        id: 'Seperti a dalam bahasa Indonesia.',
        ms: 'Seperti a dalam bahasa Melayu.',
        it: 'Come a in "casa".',
    },
    ai: {
        en: 'Similar to "eye": start with a, then glide to i.',
        de: 'Ähnlich wie ei in "mein".',
        es: 'Parecido a ai/ay, con deslizamiento claro de a a i.',
        pt: 'Parecido com ai, deslizando de a para i.',
        it: 'Come ai, passando da a a i.',
    },
    an: {
        en: 'Similar to "an" in "ban", with a clear final n.',
        fr: 'Contrairement au français "an", gardez un vrai n final avec la langue.',
        pt: 'Não nasalize apenas a vogal: termine com n claro.',
    },
    ang: {
        en: 'Similar to "ong" in "gong", but start from a.',
        de: 'Wie ein a mit ng-Auslaut, ähnlich dem Ende von "lang".',
        ru: 'Начинается с а и заканчивается задним носовым нг.',
    },
    o: {
        en: 'Round the lips, somewhat like British "or" without r.',
        fr: 'Proche de o ouvert/arrondi, mais sans r final.',
        de: 'Gerundete Lippen, ähnlich offenem o.',
        es: 'Como o, con labios redondeados.',
        pt: 'Como o, com lábios arredondados.',
        it: 'Come o, con labbra arrotondate.',
    },
    ou: {
        en: 'Similar to "oh": start with o, then glide to u.',
        fr: 'Commencez par o, puis glissez vers ou.',
        de: 'Beginne mit o und gleite zu u.',
        es: 'Empieza con o y desliza hacia u.',
        pt: 'Comece com o e deslize para u.',
        it: 'Inizia con o e scivola verso u.',
    },
    e: {
        en: 'No exact English equivalent: a mid-back vowel, deeper than schwa.',
        fr: 'Pas exactement le e français : reculez un peu la langue et ouvrez à moitié la bouche.',
        de: 'Nicht wie deutsches e: die Zunge liegt weiter hinten, der Mund ist halb offen.',
        es: 'No es la e española: la lengua va más atrás y la boca queda medio abierta.',
        ru: 'Не совсем русское э: язык немного оттянут назад, рот полуоткрыт.',
    },
    ei: {
        en: 'Similar to "ay" in "say".',
        de: 'Ähnlich wie ey/ay, aber mit chinesischem e als Start.',
        es: 'Empieza con e y desliza hacia i.',
        pt: 'Comece com e e deslize para i.',
        it: 'Inizia con e e scivola verso i.',
    },
    en: {
        en: 'Similar to "un" in "fun", with a clear final n.',
        fr: 'Gardez un vrai n final ; ne nasalisez pas seulement la voyelle comme en français.',
        pt: 'Termine com n claro; não deixe só a vogal nasal.',
    },
    eng: {
        en: 'Similar to the ending of "length", with a back nasal ng.',
        de: 'Mit ng-Auslaut wie am Ende von "lang".',
        ru: 'Заканчивается задним носовым нг, не обычным н.',
    },
    er: {
        en: 'Somewhat like British "er", but with a clearer curled tongue.',
        fr: 'Pas comme le r français : commencez par e, puis recourbez légèrement la langue.',
        de: 'Nicht wie deutsches er: beginne mit e und rolle die Zunge leicht zurück.',
        ru: 'Начните с э и слегка загните язык назад; это не раскатистое р.',
    },
    i: {
        en: 'Similar to "ee" in "see".',
        jp: '日本語の「い」に近いですが、口は横に保ちます。',
        fr: 'Comme i dans "si".',
        de: 'Wie i in "Liebe".',
        ko: '한국어 ㅣ와 가깝습니다.',
        es: 'Como i en "sí".',
        vi: 'Gần với i/y trong tiếng Việt.',
        pt: 'Como i em "sim".',
        ru: 'Как и, но губы не округляйте.',
        id: 'Seperti i dalam bahasa Indonesia.',
        ms: 'Seperti i dalam bahasa Melayu.',
        it: 'Come i in "sì".',
    },
    ie: {
        en: 'Similar to "yeah": start with i, then open to e.',
        fr: 'Commencez par i, puis ouvrez vers é/è.',
        de: 'Beginne mit i und öffne zu e.',
        es: 'Parecido a ie: empieza con i y abre hacia e.',
        it: 'Simile a ie: inizia con i e apri verso e.',
    },
    in: {
        en: 'Start with i, then end with a clear n.',
        fr: 'Ne le nasalisez pas comme le français "in" : gardez un vrai n final.',
        pt: 'Termine com n claro; não nasalize apenas a vogal.',
    },
    ing: {
        en: 'Similar to "ing" in "sing".',
        de: 'Mit ng-Auslaut wie in "Ding".',
        ru: 'Заканчивается задним носовым нг, не обычным н.',
    },
    u: {
        en: 'Similar to "oo" in "food".',
        jp: '日本語の「う」より唇をもっと丸めて前に出します。',
        fr: 'Proche de ou dans "vous".',
        de: 'Wie u in "gut", mit gerundeten Lippen.',
        ko: '한국어 ㅜ와 가깝습니다.',
        es: 'Como u en "tú", con labios redondeados.',
        vi: 'Gần với u trong tiếng Việt, môi tròn rõ.',
        pt: 'Como u em "tu", com lábios arredondados.',
        ru: 'Как у, с округлёнными губами.',
        id: 'Seperti u dalam bahasa Indonesia, dengan bibir bulat.',
        ms: 'Seperti u dalam bahasa Melayu, dengan bibir bulat.',
        it: 'Come u in "tu", con labbra arrotondate.',
    },
    ui: {
        en: 'Start with u, then glide toward ei; it often sounds like "way".',
        de: 'Beginne mit u und gleite zu ei.',
        es: 'Empieza con u y desliza hacia ei.',
        pt: 'Comece com u e deslize para ei.',
        it: 'Inizia con u e scivola verso ei.',
    },
    uo: {
        en: 'Start with u, then glide toward o.',
        fr: 'Commencez par ou, puis ouvrez vers o.',
        de: 'Beginne mit u und gleite zu o.',
        es: 'Empieza con u y desliza hacia o.',
        pt: 'Comece com u e deslize para o.',
        it: 'Inizia con u e scivola verso o.',
    },
    'ü': {
        en: 'No exact English equivalent: round your lips for "oo" while saying "ee".',
        fr: 'Très proche du u français dans "lune".',
        de: 'Sehr nah am deutschen ü in "Tür".',
        ko: '한국어 ㅟ와 비슷하지만 한 음절 안에서 더 안정적으로 유지하세요.',
        ru: 'Сделайте губы как для у, но язык держите как для и.',
    },
    'üe': {
        en: 'Start with ü, then open toward e.',
        fr: 'Commencez par le u de "lune", puis ouvrez vers é.',
        de: 'Beginne mit deutschem ü, dann öffne zu e.',
        ko: 'ㅟ에서 시작해 ㅔ 쪽으로 여는 느낌입니다.',
    },
    'ün': {
        en: 'Start with ü, then end with n.',
        fr: 'Commencez par u comme dans "lune", puis terminez par n.',
        de: 'Beginne mit ü und ende mit n.',
        ko: 'ㅟ에 가깝게 시작한 뒤 ㄴ 받침처럼 마무리합니다.',
    },
    'üan': {
        en: 'Start with ü, then glide into an.',
        fr: 'Commencez par u comme dans "lune", puis glissez vers an avec un vrai n final.',
        de: 'Beginne mit ü und gleite zu an mit klarem n.',
    },
};

const MEANING_TRANSLATIONS = {
    tall: { zh: '高的', jp: '高い', fr: 'grand', de: 'groß', ko: '키가 큰', es: 'alto', vi: 'cao', pt: 'alto', ar: 'طويل', th: 'สูง', ru: 'высокий', id: 'tinggi', ms: 'tinggi', it: 'alto' },
    'older brother': { zh: '哥哥', jp: '兄', fr: 'grand frère', de: 'älterer Bruder', ko: '형/오빠', es: 'hermano mayor', vi: 'anh trai', pt: 'irmão mais velho', ar: 'الأخ الأكبر', th: 'พี่ชาย', ru: 'старший брат', id: 'kakak laki-laki', ms: 'abang', it: 'fratello maggiore' },
    good: { zh: '好', jp: '良い', fr: 'bon', de: 'gut', ko: '좋은', es: 'bueno', vi: 'tốt', pt: 'bom', ar: 'جيد', th: 'ดี', ru: 'хороший', id: 'baik', ms: 'baik', it: 'buono' },
    'to drink': { zh: '喝', jp: '飲む', fr: 'boire', de: 'trinken', ko: '마시다', es: 'beber', vi: 'uống', pt: 'beber', ar: 'يشرب', th: 'ดื่ม', ru: 'пить', id: 'minum', ms: 'minum', it: 'bere' },
    'to see': { zh: '看', jp: '見る', fr: 'voir', de: 'sehen', ko: '보다', es: 'ver', vi: 'xem', pt: 'ver', ar: 'يرى', th: 'ดู', ru: 'видеть', id: 'melihat', ms: 'melihat', it: 'vedere' },
    'can / may': { zh: '可以', jp: 'できる', fr: 'pouvoir', de: 'können', ko: '할 수 있다', es: 'poder', vi: 'có thể', pt: 'poder', ar: 'يمكن', th: 'สามารถ', ru: 'мочь', id: 'bisa', ms: 'boleh', it: 'potere' },
    mom: { zh: '妈妈', jp: '母', fr: 'maman', de: 'Mama', ko: '엄마', es: 'mamá', vi: 'mẹ', pt: 'mãe', ar: 'أم', th: 'แม่', ru: 'мама', id: 'ibu', ms: 'ibu', it: 'mamma' },
    dad: { zh: '爸爸', jp: '父', fr: 'papa', de: 'Papa', ko: '아빠', es: 'papá', vi: 'bố', pt: 'pai', ar: 'أب', th: 'พ่อ', ru: 'папа', id: 'ayah', ms: 'ayah', it: 'papà' },
    pen: { zh: '笔', jp: 'ペン', fr: 'stylo', de: 'Stift', ko: '펜', es: 'bolígrafo', vi: 'bút', pt: 'caneta', ar: 'قلم', th: 'ปากกา', ru: 'ручка', id: 'pena', ms: 'pen', it: 'penna' },
    'to climb': { zh: '爬', jp: '登る', fr: 'grimper', de: 'klettern', ko: '오르다', es: 'trepar', vi: 'leo', pt: 'subir', ar: 'يتسلق', th: 'ปีน', ru: 'лезть', id: 'memanjat', ms: 'memanjat', it: 'arrampicarsi' },
    'to criticise': { zh: '批评', jp: '批判する', fr: 'critiquer', de: 'kritisieren', ko: '비판하다', es: 'criticar', vi: 'phê bình', pt: 'criticar', ar: 'ينتقد', th: 'วิจารณ์', ru: 'критиковать', id: 'mengkritik', ms: 'mengkritik', it: 'criticare' },
};

const getArticulationText = (symbol, lang) => {
    if (lang === 'en') return ARTICULATION_EN[symbol] || '';
    return GUIDE_TRANSLATIONS[lang]?.(symbol) || ARTICULATION_EN[symbol] || '';
};

const getNativeHint = (symbol, lang) => NATIVE_HINTS[symbol]?.[lang] || '';

const localizedMeaning = (meaning, lang) => MEANING_TRANSLATIONS[meaning]?.[lang] || meaning;

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
            className="px-4 py-2.5 border border-slate-200 rounded-xl text-lg font-mono font-semibold text-slate-700
                       hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50 active:scale-95
                       transition-all min-w-[56px] text-center"
        >
            {label}
        </button>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// INTRO PAGE
// ─────────────────────────────────────────────────────────────────────────────
function IntroPage({ onGroupClick, ui }) {
    const tableHeaders = ['', ui.initial, ui.final, ui.tone, ui.syllable, ''];

    return (
        <div className="space-y-10">
            {/* Character breakdown examples */}
            <section>
                <h2 className="text-3xl font-black text-slate-900 mb-2">{ui.introTitle}</h2>
                <p className="text-slate-500 text-lg mb-6 leading-relaxed">
                    {ui.introDesc}
                </p>
                <div className="rounded-2xl border border-slate-100 overflow-hidden shadow-sm">
                    <div className="grid grid-cols-[3rem_1fr_1fr_1fr_1fr_2.5rem] gap-x-4 px-6 py-3 bg-slate-50 border-b border-slate-100">
                        {tableHeaders.map((h, i) => (
                            <span key={i} className="text-sm font-bold text-slate-400 uppercase tracking-wide">{h}</span>
                        ))}
                    </div>
                    {INTRO_EXAMPLES.map((ex) => (
                        <div key={ex.hanzi} className="grid grid-cols-[3rem_1fr_1fr_1fr_1fr_2.5rem] gap-x-4 items-center px-6 py-4 border-b last:border-0 border-slate-50 hover:bg-slate-50/50">
                            <span className="text-3xl font-bold text-slate-800">{ex.hanzi}</span>
                            <span className="font-mono text-xl text-slate-600">{ex.initial}</span>
                            <span className="font-mono text-xl text-slate-600">{ex.final}</span>
                            <span className="font-mono text-slate-500 text-3xl">{ex.toneMark}</span>
                            <span className="font-mono text-xl font-semibold text-blue-600">{ex.syllable}</span>
                            <AudioButton audioFile={ex.audioFile} />
                        </div>
                    ))}
                </div>
            </section>

            {/* Initials + Finals side by side */}
            <div className="grid grid-cols-2 gap-x-10">
                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-2">{ui.initials}</h2>
                    <p className="text-base text-slate-400 mb-4 flex items-center gap-1.5"><Volume2 size={16} /> {ui.exploreHint}</p>
                    <div className="space-y-2">
                        {INITIALS_GROUPS.map((row, ri) => {
                            const pageId = ALL_PAGES.find(p => p.sounds.some(s => s.symbol === row[0]))?.id;
                            return (
                                <div key={ri} className="flex items-center gap-2">
                                    <div className="flex gap-2 flex-wrap flex-1">
                                        {row.map(sym => <SoundButton key={sym} label={sym} audioFile={INITIAL_AUDIO[sym]} />)}
                                    </div>
                                    {pageId && (
                                        <button onClick={() => onGroupClick(pageId)} className="shrink-0 flex items-center gap-0.5 text-sm font-semibold text-slate-400 hover:text-blue-600 hover:bg-blue-50 px-2.5 py-1.5 rounded-lg border border-slate-200 hover:border-blue-200 transition-all">
                                            {ui.detail} <ChevronRight size={14} />
                                        </button>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </section>

                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-2">{ui.finals}</h2>
                    <p className="text-base text-slate-400 mb-4 flex items-center gap-1.5"><Volume2 size={16} /> {ui.exploreHint}</p>
                    <div className="space-y-2">
                        {FINALS_GROUPS.map((row, ri) => {
                            const pageId = ALL_PAGES.find(p => p.sounds.some(s => s.symbol === row[0]))?.id;
                            return (
                                <div key={ri} className="flex items-center gap-2">
                                    <div className="flex gap-2 flex-wrap flex-1">
                                        {row.map(sym => <SoundButton key={sym} label={sym} audioFile={FINAL_AUDIO[sym]} />)}
                                    </div>
                                    {pageId && (
                                        <button onClick={() => onGroupClick(pageId)} className="shrink-0 flex items-center gap-0.5 text-sm font-semibold text-slate-400 hover:text-blue-600 hover:bg-blue-50 px-2.5 py-1.5 rounded-lg border border-slate-200 hover:border-blue-200 transition-all">
                                            {ui.detail} <ChevronRight size={14} />
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
                <h2 className="text-2xl font-black text-slate-900 mb-2">{ui.tonesTitle}</h2>
                <p className="text-slate-500 text-base mb-4 leading-relaxed">
                    {ui.tonesDesc}
                </p>
                <div className="space-y-3">
                    {TONES.map((t, index) => (
                        <div key={t.number} className="flex items-center gap-5 bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 hover:border-blue-100 transition-colors">
                            <div className="w-10 shrink-0 text-center">
                                <span className="text-5xl font-bold text-blue-500 leading-none select-none">{t.mark}</span>
                            </div>
                            <div className="flex items-center gap-3 w-28 shrink-0">
                                <span className="text-4xl font-bold text-slate-800 leading-none">{t.hanzi}</span>
                                <span className="font-mono text-xl font-semibold text-blue-600">{t.pinyin}</span>
                            </div>
                            <AudioButton audioFile={t.audioFile} />
                            <div className="flex-1 min-w-0">
                                <div className="text-base font-semibold text-slate-600">{ui.toneNames[index] || t.nameEn}</div>
                                <div className="text-base text-slate-400">{ui.toneMeanings[index] || t.meaning}</div>
                            </div>
                            <div className="shrink-0 w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center">
                                <span className="text-sm font-bold text-slate-400">{t.number}</span>
                            </div>
                        </div>
                    ))}
                </div>
                <p className="text-sm text-slate-400 mt-3">{ui.neutralNote}</p>
            </section>
        </div>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// DETAIL PAGE (one per initial group)
// ─────────────────────────────────────────────────────────────────────────────
function DetailSection({ page, onBackToTop, lang, ui }) {
    return (
        <div className="space-y-6">
            <div className="flex items-start justify-between">
                <div>
                    <h2 className="text-3xl font-black text-slate-900 font-mono tracking-widest mb-1">{page.title}</h2>
                    <p className="text-lg text-slate-500">{page.subtitle}</p>
                </div>
                <button onClick={onBackToTop} className="mt-1 shrink-0 text-sm text-slate-400 hover:text-blue-500 flex items-center gap-1 transition-colors">
                    <ChevronLeft size={14} /> {ui.overview}
                </button>
            </div>

            {page.note && (
                <div className="flex gap-3 bg-blue-50 border border-blue-100 rounded-2xl px-5 py-4">
                    <span className="text-blue-400 text-lg leading-snug shrink-0">ℹ</span>
                    <p className="text-base text-blue-700 leading-relaxed">{page.note}</p>
                </div>
            )}

            <div className="space-y-6">
                {page.sounds.map((sound) => {
                    const articulation = getArticulationText(sound.symbol, lang) || sound.description;
                    const nativeHint = getNativeHint(sound.symbol, lang) || (lang === 'en' ? sound.description : '');
                    return (
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
                                    <span className="font-mono text-xl font-bold text-slate-700">{sound.audioFile.replace('.wav', '')}</span>
                                    <AudioButton audioFile={sound.audioFile} size="sm" />
                                </div>
                                <p className="mt-1 text-xs font-black uppercase tracking-[0.16em] text-slate-300">{ui.articulation}</p>
                                <p className="text-base text-slate-500 mt-1.5 leading-relaxed">{articulation}</p>
                                {nativeHint && (
                                    <div className="mt-3 inline-flex max-w-3xl rounded-xl bg-blue-50 px-3.5 py-2.5 text-sm font-semibold leading-relaxed text-blue-700 ring-1 ring-blue-100">
                                        <span className="mr-2 text-blue-400">{ui.nativeHint}:</span>
                                        <span>{nativeHint}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                        {sound.examples?.length > 0 && (
                            <div className="flex gap-3 flex-wrap mt-3 pt-3 border-t border-slate-50">
                                {sound.examples.map((ex) => (
                                    <button
                                        key={ex.hanzi}
                                        onClick={() => ex.audioFile ? playPinyinAudio(ex.audioFile) : playTTS(ex.hanzi)}
                                        className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl bg-slate-50 hover:bg-blue-50 border border-slate-100 hover:border-blue-200 transition-all group"
                                    >
                                        <span className="text-2xl font-bold text-slate-800">{ex.hanzi}</span>
                                        <div className="text-left">
                                            <div className="font-mono text-sm text-blue-500">{ex.pinyin}</div>
                                            <div className="text-sm text-slate-400">{localizedMeaning(ex.meaning, lang)}</div>
                                        </div>
                                        <Volume2 size={14} className="text-slate-300 group-hover:text-blue-400 ml-1" />
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                )})}
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
export default function PinyinPage({ foundationNavigation, locationState: routeLocationState, navigate: routeNavigate }) {
    const { t, i18n } = useTranslation();
    const routerNavigate = useNavigate();
    const location = useLocation();
    const navigate = routeNavigate || routerNavigate;
    const locationState = routeLocationState ?? location.state;
    const introRef = useRef(null);

    // Scroll to a section, offset for sticky bars (navbar 64px + sticky bar ~52px)
    const scrollToSection = useCallback((id) => {
        const el = id === 'intro' ? introRef.current : document.getElementById(id);
        if (!el) return;
        const top = el.getBoundingClientRect().top + window.scrollY - 128;
        window.scrollTo({ top, behavior: 'smooth' });
    }, []);

    const lang = normalizeUiLang(i18n.language);
    const ui = t('pinyin_intro', { returnObjects: true });

    return (
        <div className="min-h-screen bg-slate-50 pt-16">
            <IntroFloatingNav
                currentPath="/learn/pinyin"
                locationState={locationState}
                navigate={navigate}
                t={t}
                foundationNavigation={foundationNavigation}
            />

            {/* Single scroll content */}
            <div className="max-w-4xl mx-auto px-5 py-8 space-y-20">
                {/* Overview */}
                <div ref={introRef} data-section-id="intro">
                    <IntroPage onGroupClick={scrollToSection} ui={ui} />
                </div>

                {/* All detail sections */}
                {ALL_PAGES.map((page) => (
                    <div
                        key={page.id}
                        id={page.id}
                        data-section-id={page.id}
                        className="scroll-mt-32 border-t border-slate-100 pt-12"
                    >
                        <DetailSection page={page} onBackToTop={() => scrollToSection('intro')} lang={lang} ui={ui} />
                    </div>
                ))}
            </div>
        </div>
    );
}
