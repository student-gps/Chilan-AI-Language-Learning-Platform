"""
Generate static TTS narration audio for the course intro video.

Output directory:
  frontend/public/audio/intro/

File naming follows the frontend lookup rule in CourseIntroVideo.jsx:
  EN: slide_{id}.mp3
  Others: slide_{id}_{ui_lang}.mp3

Examples:
  cd backend
  python generate_intro_narration.py
  python generate_intro_narration.py --lang fr
  python generate_intro_narration.py --lang all
  python generate_intro_narration.py --lang jp --overwrite
"""

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from content_builder.zh.integrated_chinese.tasks.narration_audio import Task4DExplanationNarrator


SUPPORTED_UI_LANGS = [
    "zh",
    "en",
    "jp",
    "fr",
    "de",
    "ko",
    "es",
    "vi",
    "pt",
    "ar",
    "th",
    "ru",
    "id",
    "ms",
    "it",
]

# Frontend uses "jp"; TTS providers and env vars use "ja".
TTS_LANG_BY_UI_LANG = {
    "jp": "ja",
}

DEFAULT_AZURE_VOICE_BY_TTS_LANG = {
    "en": "en-US-GuyNeural",
    "zh": "zh-CN-YunxiNeural",
}

SLIDE_IDS = ["welcome", "sounds", "skills", "ai", "fsrs", "start"]

NARRATIONS = {
    "zh": {
        "welcome": "欢迎来到 Chilan，一个由 AI 驱动的中文学习平台。本课程培养真实的交流能力：听、说和打字。我们从第一原理出发，先从语音系统开始。",
        "sounds": "每个汉语音节都有声调，声调一变，意思也会完全改变。四个声调分别是高平调、上升调、降升调和下降调。掌握声调，是学习中文最重要的基础。",
        "skills": "本课程训练三项核心技能：听力、口语，以及使用拼音输入法打字。我们关注中文在日常数字生活中的真实使用方式，而不是手写。很快，你就能阅读、听懂、开口说，并且打出中文。",
        "ai": "你提交的每个答案，都会经过三层系统评估。即时模式匹配处理明显情况。语义比较捕捉表达不同但意思相同的答案。大型语言模型则处理真正复杂的边界情况，并给出详细解释。",
        "fsrs": "你的复习计划由 FSRS 驱动，也就是自由间隔重复调度器。你掌握得好的内容会更少出现。比较困难的内容会更快回来。这能确保你的学习时间用在最需要的地方。",
        "start": "你已经准备好开始了。先从基础模块开始：拼音帮助你掌握语音系统，汉字帮助你理解结构。课程里的每一课，都会建立在这些基础之上。",
    },
    "en": {
        "welcome": "Welcome to Chilan, an AI-powered Chinese language learning platform. This course builds real communication skills: listening, speaking, and typing. We start from first principles, beginning with the sound system.",
        "sounds": "Every Chinese syllable has a tone, and changing the tone completely changes the meaning. The four tones are high and level, rising, falling-rising, and falling. Mastering tones is the single most important foundation in Chinese.",
        "skills": "This course trains three core skills: listening, speaking, and typing with a pinyin input method. We focus on how Chinese is actually used in daily digital life, not handwriting. You'll be able to read, listen, speak, and type before long.",
        "ai": "Every answer you submit is evaluated by a three-tier system. Instant pattern matching handles obvious cases. Semantic comparison catches answers that mean the same thing in different words. And a large language model handles genuine edge cases with a detailed explanation.",
        "fsrs": "Your review schedule is powered by FSRS, the Free Spaced Repetition Scheduler. Items you know well come back less often. Tricky items reappear sooner. This ensures you spend your study time exactly where it's needed.",
        "start": "You're ready to begin. Start with the foundation modules: pinyin for the sound system, then Chinese characters for structure. Every lesson in the course builds on these foundations.",
    },
    "jp": {
        "welcome": "Chilanへようこそ。AIを活用した中国語学習プラットフォームです。このコースでは、聞く、話す、入力するという実用的なコミュニケーション能力を育てます。まずは原理から、音の体系から始めます。",
        "sounds": "中国語のすべての音節には声調があり、声調が変わると意味も大きく変わります。四つの声調は、高く平らな音、上がる音、下がって上がる音、そして下がる音です。声調を身につけることは、中国語学習でもっとも重要な基礎です。",
        "skills": "このコースでは、聞く力、話す力、そしてピンイン入力で文字を打つ力という三つの中心スキルを鍛えます。手書きではなく、日常のデジタル生活で中国語が実際に使われる方法に集中します。まもなく、読んで、聞いて、話して、入力できるようになります。",
        "ai": "あなたが送信するすべての回答は、三段階のシステムで評価されます。明らかなケースは即時のパターン照合で処理します。意味の比較は、言い方が違っても同じ意味の回答を捉えます。そして大規模言語モデルが、本当に微妙なケースを判断し、詳しい説明を返します。",
        "fsrs": "復習スケジュールはFSRS、つまり自由間隔反復スケジューラーによって管理されます。よく覚えている項目は少ない頻度で戻ってきます。難しい項目はより早く再登場します。これにより、学習時間を本当に必要なところに使えます。",
        "start": "準備はできました。まずは基礎モジュールから始めましょう。ピンインで音の体系を学び、次に漢字で構造を理解します。コース内のすべてのレッスンは、この基礎の上に積み重なります。",
    },
    "fr": {
        "welcome": "Bienvenue sur Chilan, une plateforme d'apprentissage du chinois propulsée par l'IA. Ce cours développe de vraies compétences de communication : écouter, parler et taper. Nous partons des principes de base, en commençant par le système phonétique.",
        "sounds": "Chaque syllabe chinoise a un ton, et changer le ton change complètement le sens. Les quatre tons sont haut et plat, montant, descendant puis montant, et descendant. Maîtriser les tons est la base la plus importante du chinois.",
        "skills": "Ce cours entraîne trois compétences essentielles : écouter, parler et taper avec une méthode de saisie pinyin. Nous nous concentrons sur l'utilisation réelle du chinois dans la vie numérique quotidienne, pas sur l'écriture manuscrite. Vous pourrez bientôt lire, écouter, parler et taper.",
        "ai": "Chaque réponse que vous envoyez est évaluée par un système à trois niveaux. La correspondance instantanée gère les cas évidents. La comparaison sémantique repère les réponses qui ont le même sens avec des mots différents. Et un grand modèle de langage traite les vrais cas limites avec une explication détaillée.",
        "fsrs": "Votre calendrier de révision est alimenté par FSRS, le Free Spaced Repetition Scheduler. Les éléments que vous connaissez bien reviennent moins souvent. Les éléments difficiles réapparaissent plus vite. Cela garantit que votre temps d'étude va exactement là où il est nécessaire.",
        "start": "Vous êtes prêt à commencer. Démarrez avec les modules de base : le pinyin pour le système sonore, puis les caractères chinois pour la structure. Chaque leçon du cours s'appuie sur ces fondations.",
    },
    "de": {
        "welcome": "Willkommen bei Chilan, einer KI-gestützten Plattform zum Chinesischlernen. Dieser Kurs baut echte Kommunikationsfähigkeiten auf: Hören, Sprechen und Tippen. Wir beginnen bei den Grundlagen, zuerst mit dem Lautsystem.",
        "sounds": "Jede chinesische Silbe hat einen Ton, und ein anderer Ton kann die Bedeutung völlig verändern. Die vier Töne sind hoch und eben, steigend, fallend-steigend und fallend. Die Töne zu beherrschen ist die wichtigste Grundlage im Chinesischen.",
        "skills": "Dieser Kurs trainiert drei Kernfähigkeiten: Hören, Sprechen und Tippen mit einer Pinyin-Eingabemethode. Wir konzentrieren uns darauf, wie Chinesisch im digitalen Alltag wirklich verwendet wird, nicht auf Handschrift. Schon bald kannst du lesen, hören, sprechen und tippen.",
        "ai": "Jede Antwort, die du eingibst, wird von einem dreistufigen System bewertet. Ein sofortiger Musterabgleich behandelt klare Fälle. Der semantische Vergleich erkennt Antworten mit gleicher Bedeutung, auch wenn sie anders formuliert sind. Und ein großes Sprachmodell behandelt echte Grenzfälle mit einer ausführlichen Erklärung.",
        "fsrs": "Dein Wiederholungsplan wird von FSRS gesteuert, dem Free Spaced Repetition Scheduler. Inhalte, die du gut kannst, kommen seltener zurück. Schwierige Inhalte erscheinen früher wieder. So nutzt du deine Lernzeit genau dort, wo sie am meisten gebraucht wird.",
        "start": "Du bist bereit zu beginnen. Starte mit den Grundlagenmodulen: Pinyin für das Lautsystem und danach chinesische Schriftzeichen für die Struktur. Jede Lektion in diesem Kurs baut auf diesen Grundlagen auf.",
    },
    "ko": {
        "welcome": "Chilan에 오신 것을 환영합니다. Chilan은 AI 기반 중국어 학습 플랫폼입니다. 이 과정은 듣기, 말하기, 타이핑이라는 실제 의사소통 능력을 길러 줍니다. 우리는 가장 기본 원리부터, 먼저 소리 체계부터 시작합니다.",
        "sounds": "중국어의 모든 음절에는 성조가 있고, 성조가 바뀌면 의미도 완전히 달라질 수 있습니다. 네 가지 성조는 높고 평평한 소리, 올라가는 소리, 내려갔다 올라가는 소리, 내려가는 소리입니다. 성조를 익히는 것은 중국어 학습의 가장 중요한 기초입니다.",
        "skills": "이 과정은 세 가지 핵심 능력을 훈련합니다. 듣기, 말하기, 그리고 병음 입력기로 타이핑하기입니다. 손글씨가 아니라, 디지털 일상에서 중국어가 실제로 쓰이는 방식에 집중합니다. 곧 읽고, 듣고, 말하고, 입력할 수 있게 됩니다.",
        "ai": "여러분이 제출하는 모든 답변은 세 단계 시스템으로 평가됩니다. 즉시 패턴 매칭은 명확한 경우를 처리합니다. 의미 비교는 표현이 달라도 뜻이 같은 답변을 찾아냅니다. 그리고 대형 언어 모델은 정말 애매한 경우를 자세한 설명과 함께 판단합니다.",
        "fsrs": "복습 일정은 FSRS, 즉 자유 간격 반복 스케줄러가 관리합니다. 잘 아는 항목은 덜 자주 돌아오고, 어려운 항목은 더 빨리 다시 나타납니다. 그래서 학습 시간을 가장 필요한 곳에 쓸 수 있습니다.",
        "start": "이제 시작할 준비가 되었습니다. 먼저 기초 모듈부터 시작하세요. 병음은 소리 체계를 배우기 위한 것이고, 한자는 구조를 이해하기 위한 것입니다. 이 과정의 모든 수업은 이 기초 위에 쌓입니다.",
    },
    "es": {
        "welcome": "Bienvenido a Chilan, una plataforma para aprender chino impulsada por IA. Este curso desarrolla habilidades reales de comunicación: escuchar, hablar y escribir con el teclado. Empezamos desde los principios básicos, comenzando por el sistema de sonidos.",
        "sounds": "Cada sílaba china tiene un tono, y cambiar el tono puede cambiar completamente el significado. Los cuatro tonos son alto y plano, ascendente, descendente-ascendente y descendente. Dominar los tonos es la base más importante del chino.",
        "skills": "Este curso entrena tres habilidades centrales: escuchar, hablar y escribir con un método de entrada pinyin. Nos centramos en cómo se usa realmente el chino en la vida digital diaria, no en la escritura a mano. Pronto podrás leer, escuchar, hablar y escribir.",
        "ai": "Cada respuesta que envías se evalúa con un sistema de tres niveles. La coincidencia instantánea de patrones maneja los casos obvios. La comparación semántica detecta respuestas que significan lo mismo con palabras diferentes. Y un modelo de lenguaje grande resuelve los casos realmente ambiguos con una explicación detallada.",
        "fsrs": "Tu calendario de repaso funciona con FSRS, el programador gratuito de repetición espaciada. Los elementos que conoces bien vuelven con menos frecuencia. Los difíciles reaparecen antes. Así dedicas tu tiempo de estudio exactamente donde hace falta.",
        "start": "Ya estás listo para empezar. Comienza con los módulos de base: pinyin para el sistema de sonidos y luego caracteres chinos para la estructura. Cada lección del curso se construye sobre estos fundamentos.",
    },
    "vi": {
        "welcome": "Chào mừng bạn đến với Chilan, nền tảng học tiếng Trung được hỗ trợ bởi AI. Khóa học này xây dựng năng lực giao tiếp thật: nghe, nói và gõ. Chúng ta bắt đầu từ những nguyên lý cơ bản nhất, trước hết là hệ thống âm thanh.",
        "sounds": "Mỗi âm tiết tiếng Trung đều có thanh điệu, và khi đổi thanh điệu, nghĩa có thể thay đổi hoàn toàn. Bốn thanh là thanh cao ngang, thanh đi lên, thanh xuống rồi lên, và thanh đi xuống. Nắm vững thanh điệu là nền tảng quan trọng nhất khi học tiếng Trung.",
        "skills": "Khóa học này rèn ba kỹ năng chính: nghe, nói và gõ bằng bộ gõ pinyin. Chúng ta tập trung vào cách tiếng Trung thật sự được dùng trong đời sống số hằng ngày, không phải chữ viết tay. Không lâu nữa, bạn sẽ có thể đọc, nghe, nói và gõ tiếng Trung.",
        "ai": "Mỗi câu trả lời bạn gửi đều được đánh giá qua hệ thống ba tầng. So khớp mẫu tức thì xử lý những trường hợp rõ ràng. So sánh ngữ nghĩa nhận ra các câu trả lời khác cách diễn đạt nhưng cùng ý nghĩa. Và mô hình ngôn ngữ lớn xử lý những trường hợp thật sự tinh tế với phần giải thích chi tiết.",
        "fsrs": "Lịch ôn tập của bạn được điều khiển bởi FSRS, bộ lập lịch lặp lại ngắt quãng miễn phí. Những nội dung bạn đã nắm chắc sẽ xuất hiện ít hơn. Những phần khó sẽ quay lại sớm hơn. Nhờ vậy, thời gian học của bạn được dùng đúng vào nơi cần nhất.",
        "start": "Bạn đã sẵn sàng bắt đầu. Hãy bắt đầu với các mô-đun nền tảng: pinyin cho hệ thống âm thanh, rồi chữ Hán cho cấu trúc. Mỗi bài học trong khóa đều được xây dựng trên những nền tảng này.",
    },
    "pt": {
        "welcome": "Bem-vindo ao Chilan, uma plataforma de aprendizado de chinês com IA. Este curso desenvolve habilidades reais de comunicação: ouvir, falar e digitar. Começamos pelos princípios fundamentais, primeiro pelo sistema de sons.",
        "sounds": "Cada sílaba chinesa tem um tom, e mudar o tom pode mudar completamente o significado. Os quatro tons são alto e nivelado, ascendente, descendente-ascendente e descendente. Dominar os tons é a base mais importante do chinês.",
        "skills": "Este curso treina três habilidades centrais: ouvir, falar e digitar com um método de entrada pinyin. Focamos em como o chinês é realmente usado na vida digital diária, não na escrita à mão. Em pouco tempo, você poderá ler, ouvir, falar e digitar.",
        "ai": "Cada resposta que você envia é avaliada por um sistema de três níveis. A correspondência instantânea de padrões trata os casos óbvios. A comparação semântica reconhece respostas com o mesmo significado, mesmo com palavras diferentes. E um grande modelo de linguagem lida com casos realmente limítrofes com uma explicação detalhada.",
        "fsrs": "Seu calendário de revisão é alimentado pelo FSRS, o Free Spaced Repetition Scheduler. Itens que você conhece bem voltam com menos frequência. Itens difíceis reaparecem mais cedo. Isso garante que seu tempo de estudo seja usado exatamente onde é necessário.",
        "start": "Você está pronto para começar. Comece pelos módulos de base: pinyin para o sistema de sons e depois caracteres chineses para a estrutura. Cada lição do curso se constrói sobre essas fundações.",
    },
    "ar": {
        "welcome": "مرحبًا بك في Chilan، منصة لتعلّم الصينية مدعومة بالذكاء الاصطناعي. يبني هذا المساق مهارات تواصل حقيقية: الاستماع، والتحدث، والكتابة بلوحة المفاتيح. نبدأ من المبادئ الأساسية، بدءًا من نظام الأصوات.",
        "sounds": "لكل مقطع صوتي في الصينية نغمة، وتغيير النغمة قد يغيّر المعنى بالكامل. النغمات الأربع هي: عالية ومستوية، صاعدة، هابطة ثم صاعدة، وهابطة. إتقان النغمات هو أهم أساس في تعلّم الصينية.",
        "skills": "يدرّب هذا المساق ثلاث مهارات أساسية: الاستماع، والتحدث، والكتابة باستخدام طريقة إدخال بينيين. نركّز على الطريقة التي تُستخدم بها الصينية فعليًا في الحياة الرقمية اليومية، لا على الكتابة اليدوية. قريبًا ستتمكن من القراءة والاستماع والتحدث والكتابة.",
        "ai": "كل إجابة ترسلها تُقيّم عبر نظام من ثلاث طبقات. مطابقة الأنماط الفورية تتعامل مع الحالات الواضحة. المقارنة الدلالية تلتقط الإجابات التي تحمل المعنى نفسه بكلمات مختلفة. أما نموذج اللغة الكبير فيتعامل مع الحالات الدقيقة فعلًا ويقدّم شرحًا مفصلًا.",
        "fsrs": "يعتمد جدول المراجعة لديك على FSRS، وهو نظام مجاني لجدولة التكرار المتباعد. العناصر التي تعرفها جيدًا تعود بوتيرة أقل. والعناصر الصعبة تظهر مرة أخرى في وقت أقرب. هكذا تستخدم وقت الدراسة في المكان الذي يحتاج إليه فعلًا.",
        "start": "أنت جاهز للبدء. ابدأ بوحدات الأساس: البينيين لفهم نظام الأصوات، ثم الحروف الصينية لفهم البنية. كل درس في هذا المساق يُبنى على هذه الأسس.",
    },
    "th": {
        "welcome": "ยินดีต้อนรับสู่ Chilan แพลตฟอร์มเรียนภาษาจีนที่ขับเคลื่อนด้วย AI คอร์สนี้สร้างทักษะการสื่อสารจริง ได้แก่ การฟัง การพูด และการพิมพ์ เราเริ่มจากหลักพื้นฐาน โดยเริ่มที่ระบบเสียงก่อน",
        "sounds": "พยางค์ภาษาจีนทุกพยางค์มีวรรณยุกต์ และเมื่อเปลี่ยนวรรณยุกต์ ความหมายก็อาจเปลี่ยนไปทั้งหมด วรรณยุกต์ทั้งสี่คือ เสียงสูงเรียบ เสียงขึ้น เสียงตกแล้วขึ้น และเสียงตก การเข้าใจวรรณยุกต์คือพื้นฐานที่สำคัญที่สุดของภาษาจีน",
        "skills": "คอร์สนี้ฝึกทักษะหลักสามอย่าง คือ การฟัง การพูด และการพิมพ์ด้วยระบบป้อนพินอิน เราเน้นวิธีใช้ภาษาจีนจริงในชีวิตดิจิทัลประจำวัน ไม่ใช่การเขียนด้วยมือ อีกไม่นานคุณจะอ่าน ฟัง พูด และพิมพ์ภาษาจีนได้",
        "ai": "ทุกคำตอบที่คุณส่งจะถูกประเมินด้วยระบบสามชั้น การจับคู่รูปแบบทันทีจัดการกรณีที่ชัดเจน การเปรียบเทียบเชิงความหมายจับคำตอบที่ใช้คำต่างกันแต่มีความหมายเดียวกัน และโมเดลภาษาขนาดใหญ่จะจัดการกรณีที่ซับซ้อนจริง พร้อมคำอธิบายละเอียด",
        "fsrs": "ตารางทบทวนของคุณขับเคลื่อนด้วย FSRS หรือระบบจัดตารางทบทวนแบบเว้นระยะฟรี สิ่งที่คุณจำได้ดีจะกลับมาน้อยลง สิ่งที่ยากจะกลับมาเร็วขึ้น วิธีนี้ช่วยให้คุณใช้เวลาเรียนกับส่วนที่จำเป็นที่สุด",
        "start": "คุณพร้อมเริ่มแล้ว เริ่มจากโมดูลพื้นฐานก่อน พินอินสำหรับระบบเสียง จากนั้นตัวอักษรจีนสำหรับโครงสร้าง ทุกบทเรียนในคอร์สนี้จะต่อยอดจากพื้นฐานเหล่านี้",
    },
    "ru": {
        "welcome": "Добро пожаловать в Chilan, платформу для изучения китайского языка с поддержкой ИИ. Этот курс развивает реальные навыки общения: аудирование, говорение и набор текста. Мы начинаем с базовых принципов, прежде всего со звуковой системы.",
        "sounds": "У каждого китайского слога есть тон, и изменение тона может полностью изменить значение. Четыре тона: высокий ровный, восходящий, нисходяще-восходящий и нисходящий. Овладение тонами — самая важная основа китайского языка.",
        "skills": "Этот курс тренирует три ключевых навыка: слушать, говорить и печатать с помощью ввода пиньинь. Мы сосредоточены на том, как китайский реально используется в повседневной цифровой жизни, а не на письме от руки. Скоро вы сможете читать, слушать, говорить и печатать.",
        "ai": "Каждый ваш ответ оценивается трехуровневой системой. Мгновенное сопоставление шаблонов обрабатывает очевидные случаи. Семантическое сравнение находит ответы с тем же смыслом, даже если они сформулированы иначе. А большая языковая модель разбирает настоящие пограничные случаи и дает подробное объяснение.",
        "fsrs": "Ваш график повторения работает на FSRS, Free Spaced Repetition Scheduler. То, что вы хорошо знаете, возвращается реже. Сложные элементы появляются раньше. Так вы тратите учебное время именно там, где оно нужнее всего.",
        "start": "Вы готовы начать. Начните с базовых модулей: пиньинь для звуковой системы, затем китайские иероглифы для структуры. Каждый урок курса строится на этих основах.",
    },
    "id": {
        "welcome": "Selamat datang di Chilan, platform belajar bahasa Mandarin yang didukung AI. Kursus ini membangun keterampilan komunikasi nyata: mendengar, berbicara, dan mengetik. Kita mulai dari prinsip dasar, dimulai dengan sistem bunyi.",
        "sounds": "Setiap suku kata Mandarin memiliki nada, dan perubahan nada dapat mengubah makna sepenuhnya. Empat nada itu adalah tinggi dan datar, naik, turun lalu naik, dan turun. Menguasai nada adalah fondasi terpenting dalam bahasa Mandarin.",
        "skills": "Kursus ini melatih tiga keterampilan inti: mendengar, berbicara, dan mengetik dengan metode input pinyin. Kita berfokus pada bagaimana bahasa Mandarin benar-benar digunakan dalam kehidupan digital sehari-hari, bukan tulisan tangan. Tidak lama lagi, kamu akan bisa membaca, mendengar, berbicara, dan mengetik.",
        "ai": "Setiap jawaban yang kamu kirim dinilai oleh sistem tiga tingkat. Pencocokan pola instan menangani kasus yang jelas. Perbandingan semantik menangkap jawaban yang bermakna sama meski memakai kata berbeda. Dan model bahasa besar menangani kasus tepi yang benar-benar rumit dengan penjelasan rinci.",
        "fsrs": "Jadwal ulasanmu didukung oleh FSRS, Free Spaced Repetition Scheduler. Item yang sudah kamu kuasai muncul lebih jarang. Item yang sulit muncul kembali lebih cepat. Ini memastikan waktu belajarmu digunakan tepat di tempat yang paling dibutuhkan.",
        "start": "Kamu siap memulai. Mulailah dengan modul dasar: pinyin untuk sistem bunyi, lalu karakter Mandarin untuk struktur. Setiap pelajaran dalam kursus ini dibangun di atas fondasi tersebut.",
    },
    "ms": {
        "welcome": "Selamat datang ke Chilan, platform pembelajaran bahasa Cina yang dikuasakan oleh AI. Kursus ini membina kemahiran komunikasi sebenar: mendengar, bertutur dan menaip. Kita bermula daripada prinsip asas, iaitu sistem bunyi.",
        "sounds": "Setiap suku kata bahasa Cina mempunyai nada, dan perubahan nada boleh mengubah makna sepenuhnya. Empat nada itu ialah tinggi dan rata, menaik, turun kemudian naik, dan menurun. Menguasai nada ialah asas paling penting dalam bahasa Cina.",
        "skills": "Kursus ini melatih tiga kemahiran utama: mendengar, bertutur dan menaip menggunakan kaedah input pinyin. Kita menumpukan pada cara bahasa Cina benar-benar digunakan dalam kehidupan digital harian, bukan tulisan tangan. Tidak lama lagi, anda akan dapat membaca, mendengar, bertutur dan menaip.",
        "ai": "Setiap jawapan yang anda hantar dinilai oleh sistem tiga peringkat. Padanan corak segera mengendalikan kes yang jelas. Perbandingan semantik menangkap jawapan yang membawa makna sama walaupun dengan kata yang berbeza. Dan model bahasa besar mengendalikan kes pinggir yang benar-benar rumit dengan penjelasan terperinci.",
        "fsrs": "Jadual ulang kaji anda dikuasakan oleh FSRS, Free Spaced Repetition Scheduler. Item yang anda kuasai akan muncul dengan kurang kerap. Item yang sukar akan muncul semula lebih awal. Ini memastikan masa belajar anda digunakan tepat pada bahagian yang paling diperlukan.",
        "start": "Anda sudah bersedia untuk bermula. Mulakan dengan modul asas: pinyin untuk sistem bunyi, kemudian aksara Cina untuk struktur. Setiap pelajaran dalam kursus ini dibina di atas asas tersebut.",
    },
    "it": {
        "welcome": "Benvenuto su Chilan, una piattaforma per imparare il cinese potenziata dall'IA. Questo corso sviluppa vere abilità comunicative: ascoltare, parlare e digitare. Partiamo dai principi fondamentali, iniziando dal sistema dei suoni.",
        "sounds": "Ogni sillaba cinese ha un tono, e cambiare tono può cambiare completamente il significato. I quattro toni sono alto e piano, ascendente, discendente-ascendente e discendente. Padroneggiare i toni è la base più importante del cinese.",
        "skills": "Questo corso allena tre competenze centrali: ascoltare, parlare e digitare con un metodo di input pinyin. Ci concentriamo su come il cinese viene usato davvero nella vita digitale quotidiana, non sulla scrittura a mano. Presto sarai in grado di leggere, ascoltare, parlare e digitare.",
        "ai": "Ogni risposta che invii viene valutata da un sistema a tre livelli. Il riconoscimento immediato dei pattern gestisce i casi evidenti. Il confronto semantico coglie risposte con lo stesso significato espresse con parole diverse. E un grande modello linguistico gestisce i veri casi limite con una spiegazione dettagliata.",
        "fsrs": "Il tuo programma di ripasso è gestito da FSRS, il Free Spaced Repetition Scheduler. Gli elementi che conosci bene tornano meno spesso. Quelli difficili ricompaiono prima. Così usi il tuo tempo di studio esattamente dove serve.",
        "start": "Sei pronto per iniziare. Parti dai moduli fondamentali: pinyin per il sistema dei suoni, poi caratteri cinesi per la struttura. Ogni lezione del corso si costruisce su queste basi.",
    },
}

BACKEND_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BACKEND_DIR.parent / "frontend" / "public" / "audio" / "intro"


def build_slides(ui_lang: str) -> list[dict[str, str]]:
    texts = NARRATIONS[ui_lang]
    return [{"id": slide_id, "narration": texts[slide_id]} for slide_id in SLIDE_IDS]


def output_suffix(ui_lang: str) -> str:
    return "" if ui_lang == "en" else f"_{ui_lang}"


def configure_intro_tts_defaults(tts_lang: str) -> None:
    """Prefer Azure for intro languages that otherwise fall back to global ali."""
    lang_up = tts_lang.upper()
    provider_key = f"TTS_EXPLANATION_PROVIDER_{lang_up}"
    voice_key = f"TTS_EXPLANATION_VOICE_{lang_up}"
    default_voice = DEFAULT_AZURE_VOICE_BY_TTS_LANG.get(tts_lang)
    if default_voice and not os.environ.get(provider_key):
        os.environ[provider_key] = "azure"
    if default_voice and not os.environ.get(voice_key):
        os.environ[voice_key] = default_voice


def generate_language(
    ui_lang: str,
    *,
    overwrite: bool,
    delay: float,
    max_retries: int,
    progress_start: int,
    progress_total: int,
) -> tuple[int, int]:
    tts_lang = TTS_LANG_BY_UI_LANG.get(ui_lang, ui_lang)
    slides = build_slides(ui_lang)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    configure_intro_tts_defaults(tts_lang)
    tts = Task4DExplanationNarrator()
    tts._configure_for_lang(tts_lang)
    tts._lang = tts_lang
    print(f"Language:     {ui_lang} (tts: {tts_lang})")
    print(f"TTS provider: {tts.provider}  voice: {tts.voice}")
    print(f"Single voice: {os.environ.get('TTS_EXPLANATION_SINGLE_VOICE', '0')}")
    print(f"Retries:      {max_retries}")
    print(f"Output dir:   {OUTPUT_DIR}\n")

    suffix = output_suffix(ui_lang)
    ok, fail = 0, 0
    language_started = time.monotonic()
    for local_index, slide in enumerate(slides, start=1):
        slide_id = slide["id"]
        text = slide["narration"]
        out_path = OUTPUT_DIR / f"slide_{slide_id}{suffix}.mp3"
        progress_index = progress_start + local_index
        progress_label = f"{progress_index}/{progress_total}" if progress_total else f"{local_index}/{len(slides)}"

        if out_path.exists() and out_path.stat().st_size > 100 and not overwrite:
            size_kb = out_path.stat().st_size // 1024
            print(f"  [{progress_label}] {ui_lang}:{slide_id} SKIP -> {out_path.name} ({size_kb} KB)", flush=True)
            ok += 1
            continue

        print(
            f"  [{progress_label}] {ui_lang}:{slide_id} START -> {out_path.name} "
            f"| voice={tts.voice} | chars={len(text)}",
            flush=True,
        )
        started = time.monotonic()
        try:
            tts._synthesize(text, out_path, max_retries=max_retries)
            size_kb = out_path.stat().st_size // 1024
            elapsed = time.monotonic() - started
            print(f"      OK   {elapsed:5.1f}s -> {out_path.name} ({size_kb} KB)", flush=True)
            ok += 1
            if delay > 0:
                time.sleep(delay)
        except Exception as exc:
            elapsed = time.monotonic() - started
            print(f"      FAIL {elapsed:5.1f}s -> {exc}", flush=True)
            fail += 1

    language_elapsed = time.monotonic() - language_started
    print(f"Language {ui_lang} done: {ok} ok, {fail} failed in {language_elapsed:.1f}s.\n", flush=True)
    return ok, fail


def main():
    choices = ["all", *SUPPORTED_UI_LANGS]
    parser = argparse.ArgumentParser(description="Generate intro narration audio")
    parser.add_argument(
        "--lang",
        default="en",
        choices=choices,
        help="UI language code, or 'all' (default: en)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate files even when valid output files already exist.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Seconds to wait after each successful TTS call (default: 2.0).",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum TTS retry attempts per slide (default: 3).",
    )
    parser.add_argument(
        "--code-switch",
        action="store_true",
        help="Allow CJK chunks to switch to the configured Chinese voice. Intro narration defaults to single-voice output.",
    )
    args = parser.parse_args()

    if not args.code_switch:
        os.environ["TTS_EXPLANATION_SINGLE_VOICE"] = "1"

    langs = SUPPORTED_UI_LANGS if args.lang == "all" else [args.lang]
    progress_total = len(langs) * len(SLIDE_IDS)
    progress_offset = 0
    total_ok, total_fail = 0, 0
    for ui_lang in langs:
        ok, fail = generate_language(
            ui_lang,
            overwrite=args.overwrite,
            delay=args.delay,
            max_retries=args.max_retries,
            progress_start=progress_offset,
            progress_total=progress_total,
        )
        progress_offset += len(SLIDE_IDS)
        total_ok += ok
        total_fail += fail

    print(f"All done: {total_ok} ok, {total_fail} failed.")
    print("Frontend URL pattern: /media/intro/slide_{id}.mp3 or /media/intro/slide_{id}_{ui_lang}.mp3")
    if total_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()

