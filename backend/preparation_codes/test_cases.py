# -*- coding: utf-8 -*-

# 二分类标准：
# 1: 正确 (Correct) - 标准答案或可接受变体，语义判定应为“对”
# 0: 错误 (Incorrect) - 语义错误、关键事实错误、严重语法问题，判定应为“错”

test_suites = {
    "English_Evaluation": {
        "Q18: 你好！ (L101)": {
            "standard": "Hello!",
            "cases": [
                ("Hi!", 1),
                ("Goodbye!", 0)
            ]
        },
        "Q19: 我姓李。你呢？ (L101)": {
            "standard": "My surname is Li. And you?",
            "cases": [
                ("My surname is Li. What about you?", 1),
                ("My surname is Wang. And you?", 0),
                ("My surname is Li.", 0)
            ]
        },
        "Q20: 你叫什么名字？ (L101)": {
            "standard": "What is your name?",
            "cases": [
                ("What's your name?", 1),
                ("What is your surname?", 0),
                ("Who are you?", 0)
                ]
        },
        "Q21: 我叫李友。 (L101)": {
            "standard": "My name is Li You.",
            "cases": [
                ("I'm Li You.", 1),
                ("My name is Li.", 0),
                ("My name is You.", 0)
            ]
        },
        "Q12: 你是老师吗？ (L102)": {
            "standard": "Are you a teacher?",
            "cases": [
                ("Are you a teacher?", 1),
                ("Are you teaching?", 0),
                ("Are you a student?", 0),
                ("Do you like teaching?", 0)
            ]
        },
        "Q13: 我也是学生。 (L102)": {
            "standard": "I am a student, too.",
            "cases": [
                ("I am a student, too.", 1),
                ("I am also a student.", 1),
                ("I am a student.", 0),
                ("I am a teacher, too.", 0),
                ("I am not a student.", 0)
            ]
        },
        "Q14: 我是北京人。 (L102)": {
            "standard": "I am from Beijing.",
            "cases": [
                ("I am from Beijing.", 1),
                ("I am a Beijing person.", 1),
                ("I am from Shanghai.", 0),
                ("I am not from Beijing.", 0)
            ]
        },
        "Q15: 你呢？ (L102)": {
            "standard": "And you?",
            "cases": [
                ("And you?", 1),
                ("What about you?", 1),
                ("Who are you?", 0),
                ("How about you?", 1)
            ]
        },
        "Q23: 那是你的照片吗？ (L201)": {
            "standard": "Is that your picture?",
            "cases": [
                ("Is that your picture?", 1),
                ("Is that a picture of you?", 1),
                ("Is this your picture?", 0),
                ("Is that his picture?", 0),
                ("Is that her picture?", 0)
            ]
        },
        "Q24: 这个女孩子是谁？ (L201)": {
            "standard": "Who is this girl?",
            "cases": [
                ("Who is this girl?", 1),
                ("Who's this girl?", 1),
                ("What is this girl's name?", 0),
                ("Is this girl your sister?", 0),
                ("Is this girl your friend?", 0)
            ]
        },
        "Q25: 这个男孩子是你弟弟吗？ (L201)": {
            "standard": "Is this boy your younger brother?",
            "cases": [
                ("Is this boy your younger brother?", 1),
                ("Is this boy your older brother?", 0),
                ("Is that boy your younger brother?", 0),
                ("Is this boy your sister?", 0),
                ("Is this boy your friend?", 0),
                ("Is this boy your brother?", 0)
            ]
        },
        "Q26: 他没有女儿。 (L201)": {
            "standard": "He doesn't have a daughter.",
            "cases": [
                ("He doesn't have a daughter.", 1),
                ("He has a daughter.", 0),
                ("He doesn't have a son.", 0),
                ("He has no children.", 0),
                ("He has no daughter.", 1)
            ]
        },
        "Q19: 你家有几口人? (L202)": {
            "standard": "How many people are in your family?",
            "cases": [
                ("How many persons are in your family?", 1),
                ("How many people are in your family?", 1),
                ("How many people do you have in your family?", 1),
                ("How many people are there in your family?", 1),
                ("How many people is in your family?", 0),
                ("How many people are in your home?", 0)
            ]
        },
        "Q20: 我妈妈也是老师,我爸爸是医生。 (L202)": {
            "standard": "My mom is also a teacher, and my dad is a doctor.",
            "cases": [
                ("My mom is also a teacher, and my dad is a doctor.", 1),
                ("My mom is also a doctor, and my dad is a teacher.", 0),
                ("My mom is also a teacher, and my dad is also a doctor.", 0),
                ("My mom is a teacher too, while my dad is a doctor.", 1)
            ]
        },
        "Q21: 白英爱有两个妹妹。 (L202)": {
            "standard": "Bai Ying'ai has two younger sisters.",
            "cases": [
                ("Bai Ying'ai has two younger sisters.", 1),
                ("Bai Ying'ai has two older sisters.", 0),
                ("Bai Ying'ai has two sisters.", 0),
                ("Bai Ying'ai has two younger brothers.", 0)
            ]
        },
        "Q22: 王朋没有哥哥, 李友也没有哥哥。 (L202)": {
            "standard": "Wang Peng doesn't have an older brother, and Li You doesn't have one either.",
            "cases": [
                ("Wang Peng doesn't have an older brother, and Li You doesn't have one either.", 1),
                ("Wang Peng has an older brother, but Li You doesn't have one.", 0),
                ("Wang Peng doesn't have an older brother, but Li You has one.", 0),
                ("Wang Peng has an older brother, and Li You has one too.", 0)
            ]
        },
        "Q34: 九月十二号是星期几? (L301)": {
            "standard": "What day of the week is September 12th?",
            "cases": [
                ("What day of the week is September 12th?", 1),
                ("What day is September 12th?", 0),
                ("When is September 12th?", 0),
                ("What date is it on September 12th?", 0)
            ]
        },
        "Q35: 我星期四请你吃饭,怎么样? (L301)": {
            "standard": "I'll treat you to a meal on Thursday, how about that?",
            "cases": [
                ("I'll treat you to a meal on Thursday, how about that?", 1),
                ("How about I treat you to a meal on Thursday?", 1),
                ("I will treat you to a meal on Thursday, how about that?", 1),
                ("I will treat you to a meal on Thursday, how about it?", 1),
                ("I will treat you to a meal on Tuesday, what do you think?", 0)
            ]
        },
        "Q36: 你今年多大? (L301)": {
            "standard": "How old are you this year?",
            "cases": [
                ("How old are you this year?", 1),
                ("How old are you?", 1),
                ("What is your age?", 1),
                ("How old is you?", 0)
            ]
        },
        "Q37: 我是英国人,可是我喜欢吃中国菜。 (L301)": {
            "standard": "I am British, but I like Chinese food.",
            "cases": [
                ("I am British, but I like Chinese food.", 1),
                ("I am British, but I don't like Chinese food.", 0),
                ("I am not British, but I like Chinese food.", 0),
                ("I am British, and I like Chinese food.", 0)
            ]
        },
        "Q16: 现在几点? (L302)": {
            "standard": "What time is it now?",
            "cases": [
                ("What's the time now?", 1),
                ("What's the time now?", 1),
                ("What is it now?", 0),
                ("When is it now?", 1)
            ]
        },
        "Q17: 你今天很忙,明天忙不忙? (L302)": {
            "standard": "Are you busy today? Will you be busy tomorrow?",
            "cases": [
                ("Are you busy today? Will you be busy tomorrow?", 1),
                ("Are you busy today and tomorrow?", 0),
                ("Are you busy today? Will you be free tomorrow?", 0)
            ]
        },
        "Q18: 你为什么请我吃饭? (L302)": {
            "standard": "Why are you treating me to dinner?",
            "cases": [
                ("Why do you treat me to dinner?", 1),
                ("Why do you want to treat me to dinner?", 1),
                ("Why are you treating me to lunch?", 0)
            ]
        },
        "Q19: 还请我的同学李友。 (L302)": {
            "standard": "I'm also inviting my classmate Li You.",
            "cases": [
                ("I'm inviting my classmate Li You too.", 1),
                ("I'm also inviting my friend Li You.", 0)
            ]
        },
        "Q30: 你周末喜欢做什么？ (L401)": {
            "standard": "What do you like to do on weekends?",
            "cases": [
                ("What do you like to do on weekends", 1),
                ("What do you want to do on weekends?", 0),
                ("What are you doing on weekends?", 0)
            ]
        },
        "Q31: 你喜欢不喜欢看电影？ (L401)": {
            "standard": "Do you like to watch movies or not?",
            "cases": [
                ("Do you like watching movies?", 1),
                ("Do you like watching movies or not?", 1),
                ("Do you love to watch movies?", 1),
                ("Do you want to watch movies?", 0)
            ]
        },
        "Q32: 为什么你请客？ (L401)": {
            "standard": "Why is it your treat?",
            "cases": [
                ("Why are you treating?", 1),
                ("Why do you treat me?", 1),
                ("Why are you treating me?", 0)
            ]
        },
        "Q33: 因为昨天你请我吃饭,所以今天我请你看电影。 (L401)": {
            "standard": "Because you treated me to dinner yesterday, so today I'm treating you to a movie.",
            "cases": [
                ("Because you treated me to dinner yesterday, I'm treating you to a movie today.", 1),
                ("Because you treated me a dinner yesterday, so today I'm treating you to a movie.", 1),
                ("Because you treated me to dinner yesterday, so today I'm treating you to a meal.", 0)
            ]
        },
        "Q19: 好久不见，你好吗？ (L402)": {
            "standard": "Long time no see. How are you?",
            "cases": [
                ("It's been a long time. How are you?", 1),
                ("Long time no see. How have you been?", 1),
                ("Long time no see. How do you do?", 0)
            ]
        },
        "Q21: 这个周末你想做什么？ (L402)": {
            "standard": "What do you want to do this weekend?",
            "cases": [
                ("What do you want to do on this weekend?", 1),
                ("What are you doing this weekend?", 0),
                ("What do you like to do this weekend?", 1)
            ]
        },
        "Q22: 我觉得看球没有意思。 (L402)": {
            "standard": "I think watching a ball game is not interesting.",
            "cases": [
                ("I think watching a ball game isn't interesting.", 1),
                ("I think it's not interesting to watch a ball game.", 1),
                ("I think it's boring to watch a ball game.", 1),
                ("I think watching a ball game is boring.", 0)
            ]
        },
        "Q23: 我只想吃饭、睡觉。 (L402)": {
            "standard": "I only want to eat and sleep.",
            "cases": [
                ("I want to eat and sleep only.", 1),
                ("I only want to eat.", 0)
            ]
        },
        "Q28: 认识你很高兴。 (L501)": {
            "standard": "Pleased to meet you.",
            "cases": [
                ("Nice to meet you.", 1),
                ("It's nice to meet you.", 1),
                ("I'm glad to meet you.", 1),
                ("Please, meet you.", 0),
            ]
        },
        "Q29: 你在哪儿工作? (L501)": {
            "standard": "Where do you work?",
            "cases": [
                ("Where are you working?", 1),
                ("Where do you work at?", 0),
                ("When do you work?", 0),
                ("How do you work?", 0)
            ]
        },
        "Q30: 我要一瓶可乐,可以吗? (L501)": {
            "standard": "I'd like a bottle of cola, is that okay?",
            "cases": [
                ("I want a bottle of cola, is that okay?", 1),
                ("I want a bottle of cola, can I?", 1),
                ("I want a bottle of coke, is that ok?", 0)
            ]
        },
        "Q31: 那给我一杯水吧。 (L501)": {
            "standard": "In that case, please give me a glass of water.",
            "cases": [
                ("In that case, please give me a glass of juice.", 0),
                ("Then give me a glass of water.", 1),
                ("Then give me a bottle of water.", 0)
            ]
        },
        "Q12: 王朋喝了两杯茶。 (L502)": {
            "standard": "Wang Peng drank two cups of tea.",
            "cases": [
                ("Wang Peng drank two cups of tea.", 1),
                ("Wang Peng drank two glasses of tea.", 0),
                ("Wang Peng drank a cup of tea.", 0)
            ]
        },
        "Q13: 他们一起聊天儿、看电视。 (L502)": {
            "standard": "They chatted and watched TV together.",
            "cases": [
                ("They chatted and watched TV together.", 1),
                ("They chatted together and watched TV.", 1),
                ("They chatted together but didn't watch TV.", 0)
            ]
        },
        "Q14: 我们十点钟回家。 (L502)": {
            "standard": "We go home at ten o'clock.",
            "cases": [
                ("We go home at ten o'clock.", 1),
                ("We go home at 10:00.", 1),
                ("We go home at nine o'clock.", 0)
            ]
        },
        "Q35: 喂,请问,常老师在吗？ (L601)": {
            "standard": "Hello, may I ask, is Teacher Chang in?",
            "cases": [
                ("Hello, may I ask, is Chang in?", 0),
                ("Hello, may I ask, is Teacher Chang there?", 1),
                ("Hello, may I ask if Teacher Chang is available?", 1),
                ("Hello, may I ask, is Teacher Chen here?", 0)
            ]
        },
        "Q36: 老师,今天下午您有时间吗？ (L601)": {
            "standard": "Teacher, do you have time this afternoon?",
            "cases": [
                ("Teacher, are you free this afternoon?", 1),
                ("Teacher, do you have some time this afternoon?", 1),
                ("Teacher, do you have time this evening?", 0),
                ("Teacher, do you have time tomorrow?", 0)
            ]
        },
        "Q37: 您什么时候有空儿？ (L601)": {
            "standard": "When will you have free time?",
            "cases": [
                ("When will you have free time?", 1),
                ("When are you free?", 1),
                ("When do you have free time?", 1),
                ("When will you be available?", 1),
                ("When do you have time?", 0)
            ]
        },
        "Q38: 要是您方便,四点半我到您的办公室去,行吗？ (L601)": {
            "standard": "If it's convenient for you, I'll go to your office at 4:30, is that okay?",
            "cases": [
                ("If it's convenient for you, I'll visit your office at 4:30, is that okay?", 1),
                ("If it's convenient for you, I'll come to your office at 4:30, is that okay?", 1),
                ("If it's convenient for you, I'll go to your office at 5:00, is that okay?", 0),
                ("If you're convenient, I'll go to your office at 4:40, is that okay?", 0)
            ]
        },
        "Q16: 喂,请问,王朋在吗? (L602)": {
            "standard": "Hello, is Wang Peng there?",
            "cases": [
                ("Hello, is Wang Peng in?", 1),
                ("Hello, is Wang Peng available?", 1),
                ("Hello, is Wang here?", 0)
            ]
        },
        "Q17: 好啊,但是你得请我喝咖啡。 (L602)": {
            "standard": "Sure, but you must treat me to coffee.",
            "cases": [
                ("Sure, but you have to treat me to coffee.", 1),
                ("Sure, but you must treat me to tea.", 0),
                ("Sure, but you have to treat me to tea.", 0)
            ]
        },
        "Q18: 我下个星期要考中文。 (L602)": {
            "standard": "I have a Chinese test next week.",
            "cases": [
                ("I'm going to have a Chinese test next week.", 1),
                ("I have a Chinese test next week.", 1),
                ("I have a Chinese test this week.", 0),
                ("I have a math test next week.", 0)
            ]
        },
        "Q19: 考试以后我请你看电影。 (L602)": {
            "standard": "I'll treat you to a movie after the test.",
            "cases": [
                ("I'll treat you to a movie after the exam.", 1),
                ("I'll treat you to a movie before the exam.", 0)
            ]
        },
        "Q27: 因为你帮我复习,所以考得不错。 (L701)": {
            "standard": "Because you helped me review, I did pretty well.",
            "cases": [
                ("As you helped me review, I did pretty well.", 1),
                ("Because you helped me review, I didn't do well.", 0)
            ]
        },
        "Q28: 但是我写中国字写得太慢了！ (L701)": {
            "standard": "But I write Chinese characters too slowly!",
            "cases": [
                ("But I write Chinese characters very slowly!", 1),
                ("But I write Chinese characters too fast!", 0)
            ]
        },
        "Q29: 你写字写得真好,真快。 (L701)": {
            "standard": "You write characters really well, and so fast.",
            "cases": [
                ("You write really well and fast.", 1),
                ("You write characters really well, but so slowly.", 0),
                ("You write very well, and so fast!", 1)
            ]
        },
        "Q30: 第七课的语法很容易,可是生词太多。 (L701)": {
            "standard": "The grammar for Lesson Seven is easy, but there are too many new words.",
            "cases": [
                ("The grammar for Lesson Seven is difficult, but there are too many new words.", 0),
                ("The grammar for Lesson Seven is easy, and there are not many new words.", 0),
                ("The grammar for Lesson Seven is easy but there are too many new words.", 1)
            ]
        },
        "Q16: 你平常来得很早，今天怎么这么晚？ (L702)": {
            "standard": "You usually come very early. How come you are so late today?",
            "cases": [
                ("You usually come very early. Why are you so late today?", 1),
                ("You usually come very early. How come you are so early today?", 0),
                ("You usually come very late. How come you are so late today?", 0)
            ]
        },
        "Q17: 我昨天十点就睡了。 (L702)": {
            "standard": "I went to bed at ten yesterday.",
            "cases": [
                ("I went to bed at ten p.m. yesterday.", 1),
                ("I went to bed at nine p.m. yesterday.", 0),
                ("I went to bed at eleven p.m. yesterday.", 0)
            ]
        },
        "Q18: 有个中国朋友真好。 (L702)": {
            "standard": "It's great to have a Chinese friend.",
            "cases": [
                ("It's so good to have a Chinese friend.", 1),
                ("It's great to have Chinese friends.", 0),
                ("It's not great to have a Chinese friend.", 0)
            ]
        },
        "Q19: 他很帅，很酷。 (L702)": {
            "standard": "He is very handsome and cool.",
            "cases": [
                ("He is so handsome and cool.", 1),
                ("He is very handsome but not cool.", 0),
                ("He is not very handsome but cool.", 0)

            ]
        },
        "Q25: 我一边吃饭,一边听录音。 (L801)": {
            "standard": "While I was eating, I listened to the sound recording.",
            "cases": [
                ("When I was eating, I listened to the sound recording.", 1),
                ("I listened to the sound recording while I was eating.", 1),
                ("While I was eating, I listened to music.", 0),
                ("While I was eating, I watched TV.", 0)
            ]
        },
        "Q26: 下午我到图书馆去上网。 (L801)": {
            "standard": "In the afternoon, I went to the library to go online.",
            "cases": [
                ("I went to the library to use the internet in the afternoon.", 1),
                ("In the afternoon, I went to the library to use the internet.", 1),
                ("In the evening, I went to the library to use the internet.", 0),
                ("In the afternoon, I went to the library to read books.", 0)
            ]
        },
        "Q27: 我们一边吃,一边练习说中文。 (L801)": {
            "standard": "While we were eating, we practiced speaking Chinese.",
            "cases": [
                ("When we were eating, we practiced speaking Chinese.", 1),
                ("We practiced speaking Chinese while we were eating.", 1),
                ("While we were eating, we practiced writing Chinese.", 0),
                ("While we were eating, we practiced listening to Chinese.", 0)
            ]
        },
        "Q28: 老师教我们发音、生词和语法。 (L801)": {
            "standard": "The teacher taught us pronunciation, new words, and grammar.",
            "cases": [
                ("The teacher taught us pronunciation, new words, and grammar.", 1),
                ("The teacher taught us pronunciation, new words, but not grammar.", 0),
                ("The teacher taught us pronunciation, grammar, and new words.", 1),
                ("The teacher taught us new words and grammar, but not pronunciation.", 0)
            ]
        },
        "Q17: 这个学期我很忙,除了专业课以外,还得学中文。 (L802)": {
            "standard": "I'm very busy this semester. Besides my major courses, I also have to study Chinese.",
            "cases": [
                ("I am very busy this semester. Besides my major courses, I have to learn Chinese too.", 1),
                ("I'm very busy this semester. Besides my major courses, I also have to study math.", 0),
                ("I'm very busy this semester. Besides my major courses, I also have to study Chinese and math.", 0)
            ]
        },
        "Q18: 开始我觉得很难,后来王朋常常帮我练习中文,就觉得不难了。 (L802)": {
            "standard": "At the beginning, I felt it was very difficult. Later, Wang Peng often helped me practice Chinese, so I don't feel it's difficult anymore.",
            "cases": [
                ("In the beginning, I felt it was very difficult. Wang Peng often helped me practice Chinese later, so I don't feel it's difficult anymore.", 1),
                ("At the beginning, I felt it was very difficult. Later, Wang Peng often helped me practice Chinese, but I still feel it's difficult.", 0),
                ("At the beginning, I felt it was very difficult. Later, Wang Peng often helped me practice Chinese, so I feel it's easy now.", 1)
            ]
        },
        "Q19: 我用中文写信写得很不好,请别笑我。 (L802)": {
            "standard": "I don't write well in Chinese, please don't laugh at me.",
            "cases": [
                ("I don't write well in Chinese, don't laugh at me please.", 1),
                ("I can't write well in Chinese, please don't laugh at me.", 1),
                ("I write well in Chinese, please don't laugh at me.", 0)
            ]
        },
        "Q20: 李友下午3点去图书馆上网。 (L802)": {
            "standard": "Li You goes to the library to use the internet at 3:00 PM.",
            "cases": [
                ("Li You goes to the library to use the internet at 3 p.m.", 1),
                ("Li You goes to the library to surf the internet at 3:00 PM.", 1),
                ("Li You goes to the library to use the internet at 4:00 PM.", 0),
                ("Li You goes to the library to read books at 3:00 PM.", 0)
            ]
        },
        "Q31: 您要买什么衣服？ (L901)": {
            "standard": "What clothes would you like to buy?",
            "cases": [
                ("What clothes do you want to buy?", 1),
                ("What clothes are you going to buy?", 1),
                ("What clothes do you like?", 0),
                ("What clothes do you want?", 0)
            ]
        },
        "Q32: 您喜欢什么颜色的？ (L901)": {
            "standard": "What color do you like?",
            "cases": [
                ("What color do you want?", 1),
                ("What color do you prefer?", 1),
                ("What color do you need?", 0)
            ]
        },
        "Q33: 这条裤子怎么样？ (L901)": {
            "standard": "How about this pair of pants?",
            "cases": [
                ("How about this pair of trousers?", 1),
                ("How do you like this pair of pants?", 1),
                ("How about this pair of jeans?", 0),
                ("How about this pair of shoes?", 0)
            ]
        },
        "Q34: 找您四十五块五毛一。 (L901)": {
            "standard": "Here's your change, forty-five fifty-one.",
            "cases": [
                ("Here's your change, forty-five dollars and fifty-one cents.", 1),
                ("Here's your forty-five dollars and fifty-one cents for change.", 1),
                ("Here's your change, forty-five dollars and fifty cents.", 0),
                ("Here's your change, forty-five dollars and fifty-two cents.", 0)
            ]
        },
        "Q22: 对不起，这双鞋太小了。能不能换一双？ (L902)": {
            "standard": "Excuse me, this pair of shoes is too small. Can I exchange them for another pair?",
            "cases": [
                ("Excuse me, this pair of shoes is too small for me. Could I exchange them for another pair?", 1),
                ("Excuse me, this pair of shoes is too small. Can I exchange them?", 1),
                ("Excuse me, this pair of shoes is too small. Can I return them?", 0),
                ("Excuse me, this pair of shoes is too small. Can I get a refund?", 0)
            ]
        },
        "Q23: 这双鞋虽然大小合适，可是颜色不好。 (L902)": {
            "standard": "Although this pair is the right size, the color is not good.",
            "cases": [
                ("Though this pair is the right size, the color is not good.", 1),
                ("This pair is the right size, but the color is not good.", 1),
                ("Although this pair is the right size, the color is good.", 0),
                ("This pair is the right size and the color is good.", 0)
            ]
        },
        "Q24: 你们这儿可以刷卡吗？ (L902)": {
            "standard": "Can I use a credit card here?",
            "cases": [
                ("May I use a credit card here?", 1),
                ("Do you accept credit cards?", 1),
                ("Can I pay with a credit card here?", 1),
                ("Can I use cash here?", 0)
            ]
        },
        "Q25: 你的电脑跟我的电脑一样贵。 (L902)": {
            "standard": "Your computer is as expensive as my computer.",
            "cases": [
                ("Your computer is as expensive as mine.", 1),
                ("Your computer is more expensive than my computer.", 0),
                ("Your computer is less expensive than my computer.", 0)
            ]
        },
        "Q32: 飞机票你买了吗? (L1001)": {
            "standard": "Have you bought the plane ticket?",
            "cases": [
                ("Have you bought the flight ticket?", 1),
                ("Did you buy the plane ticket?", 1),
                ("Have you bought the train ticket?", 0)
            ]
        },
        "Q33: 我想坐公共汽车或者坐地铁。 (L1001)": {
            "standard": "I'm thinking of taking the bus or the subway.",
            "cases": [
                ("I'm thinking to take the bus or the subway.", 1),
                ("I want to take the bus or the subway.", 1),
                ("I want to take the bus and the subway.", 0),
                ("I want to take a taxi.", 0)
            ]
        },
        "Q34: 王朋常常先做功课，再看电视。 (L1001)": {
            "standard": "Wang Peng often does his homework first, and then watches TV.",
            "cases": [
                ("Wang Peng often does his homework first, and watches TV then.", 1),
                ("Wang Peng often does his homework first, and then he watches TV.", 1),
                ("Wang Peng often do his homework first, and then he watch TV.", 0),
                ("Wang Peng often does his homework first, and then he watchs TV.", 0)
            ]
        },
        "Q35: 明天下午我们去打球还是去跳舞？ (L1001)": {
            "standard": "Shall we go play ball or go dancing tomorrow afternoon?",
            "cases": [
                ("Shall we go playing ball or go dancing tomorrow afternoon?", 1),
                ("Shall we go play ball and go dancing tomorrow morning?", 0)
            ]
        },
        "Q20: 我在高速公路上开车。 (L1002)": {
            "standard": "I drive on the highway.",
            "cases": [
                ("I am driving on the highway.", 1),
                ("I drive on the way.", 0)
            ]
        },
        "Q21: 王律师坐飞机去纽约。 (L1002)": {
            "standard": "Lawyer Wang takes a plane to New York.",
            "cases": [
                ("Lawyer Wang takes a flight to New York.", 1),
                ("Lawyer Wang takes a bus to New York.", 0),
                ("Lawyer Wang takes a train to New York.", 0),
                ("Lawyer Wang takes a plane to Los Angeles.", 0)
            ]
        },
        "Q22: 白英爱的鞋很漂亮。 (L1002)": {
            "standard": "Bai Ying'ai's shoes are very pretty.",
            "cases": [
                ("Bai Ying'ai's shoes are pretty.", 1),
                ("Bai Ying'ai's shoes are very beautiful.", 1),
                ("Bai Ying'ai's shoes are ugly.", 0)
            ]
        },
        "Q23: 坐飞机去纽约。 (L1002)": {
            "standard": "Take a plane to New York.",
            "cases": [
                ("Take a flight to New York.", 1),
                ("Take a bus to New York.", 0),
                ("Take a train to New York.", 0),
                ("Take a plane to Los Angeles.", 0)
            ]
        },
    },
    
    "Chinese_Evaluation": {
        "Q39: Excuse me, what is your surname? (L101)": {
            "standard": "请问，你贵姓？",
            "cases": [
                ("请问，你贵姓？", 1),
                ("请问，你叫什么名字？", 0),
                ("请问，你是谁？", 0),
                ("请问，你叫什么？", 0)
            ]
        },
        "Q40: My name is Wang Peng. (L101)": {
            "standard": "我叫王朋。",
            "cases": [
                ("我叫王朋。", 1),
                ("我的名字叫王朋。", 1),
                ("我的名字是王朋。", 1),
                ("我叫李友。", 0)
            ]
        },
        "Q41: And you? (L101)": {
            "standard": "你呢？",
            "cases": [
                ("你呢？", 1),
                ("你叫什么名字？", 0),
                ("你叫什么？", 0),
                ("你怎么样？", 1)
            ]
        },
        "Q27: I am not a teacher, I am a student. (L102)": {
            "standard": "我不是老师,我是学生。",
            "cases": [
                ("我不是老师,我是学生。", 1),
                ("我不是学生,我是老师。", 1),
                ("我不是老师,我也是学生。", 0),
                ("我不是老师。", 0),
                ("我是学生。", 0)
            ]
        },
        "Q28: Are you Chinese? (L102)": {
            "standard": "你是中国人吗？",
            "cases": [
                ("你是中国人吗？", 1),
                ("你是美国人吗？", 0),
                ("你是中国人。", 0),
                ("你是亚洲人吗？", 0),
                ("你来自中国吗？", 1)
            ]
        },
        "Q29: Yes, I am from New York. (L102)": {
            "standard": "是,我是纽约人。",
            "cases": [
                ("是的,我是纽约人。", 1),
                ("是,我来自纽约。", 1),
                ("是,我是美国人。", 0),
                ("不是,我是纽约人。", 0),
                ("是,我是纽约人。", 1)
            ]
        },
        "Q49: This is my dad, this is my mom. (L201)": {
            "standard": "这是我爸爸,这是我妈妈。",
            "cases": [
                ("这是我爸爸,这是我妈妈。", 1),
                ("这是我爸爸,那是我妈妈。", 0),
                ("那是我爸爸,这是我妈妈。", 0),
                ("这是我的父亲,这是我的母亲。", 1),
                ("这是我爸，这是我妈。", 1)
            ]
        },
        "Q50: She is my older sister. (L201)": {
            "standard": "她是我姐姐。",
            "cases": [
                ("她是我的姐姐。", 1),
                ("她是我哥哥。", 0),
                ("她是我妹妹。", 0),
                ("她是我姐姐吗？", 0),
                ("她是我姐姐！", 1)
            ]
        },
        "Q51: No, he is my oldest brother's son. (L201)": {
            "standard": "不是,他是我大哥的儿子。",
            "cases": [
                ("不是,他是我哥哥的儿子。", 1),
                ("不是,他是我弟弟的儿子。", 0),
                ("不是,他是我姐姐的儿子。", 0),
                ("是的,他是我大哥的儿子。", 0),
                ("不,他是我大哥的儿子！", 1)
            ]
        },
        "Q52: Do you have an older brother? (L201)": {
            "standard": "你有哥哥吗?",
            "cases": [
                ("你有哥哥吗?", 1),
                ("你有弟弟吗?", 0),
                ("你有姐姐吗?", 0),
                ("你有兄弟吗?", 0),
                ("你有哥哥？", 1)
            ]
        },
        "Q41: My dad is a lawyer, my mom is an English teacher. (L202)": {
            "standard": "我爸爸是律师,妈妈是英文老师。",
            "cases": [
                ("我爸爸是位律师,妈妈是个英文老师。", 1),
                ("我爸爸是律师,妈妈是老师。", 0),
                ("我爸爸是律师,妈妈是英文老师吗？", 0),
                ("我爸爸是律师,妈妈也是律师。", 0),
                ("我爸是律师,我妈是英文老师！", 1)
            ]
        },
        "Q42: What do your dad and mom do for work? (L202)": {
            "standard": "你爸爸妈妈做什么工作?",
            "cases": [
                ("你爸爸妈妈做的什么工作?", 1),
                ("你爸爸妈妈是做什么的?", 1),
                ("你爸爸妈妈的工作是什么?", 1),
                ("你爸爸妈妈是做什么工作的?", 1),
                ("你爸妈干什么的？", 1),
                ("你爷爷奶奶做什么工作？", 0),
                ("你爸爸妈妈平时做什么？", 0)
            ]
        },
        "Q43: Wang Peng is a student, and Li You is also a student. (L202)": {
            "standard": "王朋是学生, 李友也是学生。",
            "cases": [
                ("王朋是个学生, 李友也是学生。", 1),
                ("王朋是学生, 李友是学生吗？", 0),
                ("王朋是学生, 李友也是学生吗？", 0),
                ("王朋是学生, 李友也是个学生。", 1),
                ("王朋是学生, 李友不是学生。", 0)
            ]
        },
        "Q44: There are five people in my family. (L202)": {
            "standard": "我家有五口人。",
            "cases": [
                ("我家有五口人。", 1),
                ("我家有五个人。", 1),
                ("我家有五口人吗？", 0),
                ("我家有四口人。", 0),
                ("我家有五口人！", 1)
            ]
        },
        "Q71: That day is my birthday. (L301)": {
            "standard": "那天是我的生日。",
            "cases": [
                ("那天是我的生日。", 1),
                ("那天是我的生日吗？", 0),
                ("昨天是你的生日。", 0),
                ("那天是我的生日！", 1),
                ("那天是你的生日。", 0),
                ("昨天是我的生日。", 0)
            ]
        },
        "Q72: Do you like Chinese food or American food? (L301)": {
            "standard": "你喜欢吃中国菜还是美国菜？",
            "cases": [
                ("你喜欢吃中国菜还是美国菜？", 1),
                ("你喜欢吃美国菜还是中国菜？", 1),
                ("你喜欢吃中国菜吗？", 0),
                ("你喜欢吃美国菜吗？", 0),
                ("你喜欢吃什么菜？", 0),
                ("你爱吃中国菜还是美国菜？", 1)
            ]
        },
        "Q73: How about seven-thirty? (L301)": {
            "standard": "七点半怎么样？",
            "cases": [
                ("七点半怎么样？", 1),
                ("七点三十怎么样？", 0),
                ("七点怎么样？", 0),
                ("八点半怎么样？", 0)
            ]
        },
        "Q74: Okay, see you Thursday evening. (L301)": {
            "standard": "好,星期四晚上见。",
            "cases": [
                ("好的,星期四晚上见。", 1),
                ("好,星期四见。", 0),
                ("好,星期五晚上见。", 0),
                ("好,星期四晚上见！", 1)
            ]
        },
        "Q35: I have something to do at a quarter past six. (L302)": {
            "standard": "我六点一刻有事儿。",
            "cases": [
                ("我六点十五有点事情。", 1),
                ("你六点一刻有事儿。", 1),
                ("我六点有事儿。", 0),
                ("我六点三刻有事儿。", 0)
            ]
        },
        "Q36: I'd like to treat you to dinner tomorrow. How about it? (L302)": {
            "standard": "明天我请你吃晚饭,怎么样?",
            "cases": [
                ("明晚我请你吃饭如何？", 1),
                ("明天我请你吃晚饭好吗?", 1),
                ("明天我请你吃午饭怎么样?", 0)
            ]
        },
        "Q37: Because tomorrow is Gao Wenzhong's birthday. (L302)": {
            "standard": "因为明天是高文中的生日。",
            "cases": [
                ("因为明天是高文中的生日", 1),
                ("因为明天是高文中的生日吗？", 0),
                ("因为明天是高文中的生日！", 1)
            ]
        },
        "Q38: OK, see you at seven-thirty tomorrow. (L302)": {
            "standard": "好,明天七点半见。",
            "cases": [
                ("好的,明天七点半见。", 1),
                ("好,明天七点三十分见。", 1),
                ("好,明天七点见。", 0),
                ("好,明天八点半见。", 0)
            ]
        },
        "Q63: I like to sing, dance, and also like to listen to music. (L401)": {
            "standard": "我喜欢唱歌、跳舞,还喜欢听音乐。",
            "cases": [
                ("我喜欢唱歌、跳舞和听音乐。", 1),
                ("我喜欢唱歌、跳舞,也喜欢听音乐。", 1),
                ("我喜欢唱歌、跳舞,但不喜欢听音乐。", 0)
            ]
        },
        "Q64: I often watch movies on weekends. (L401)": {
            "standard": "我周末常常看电影。",
            "cases": [
                ("我常常在周末看电影。", 1),
                ("我周末经常看电影。", 1),
                ("我周末偶尔看电影。", 0),
                ("我周末看电影吗？", 0)
            ]
        },
        "Q65: Let's go see a movie tomorrow night, OK? (L401)": {
            "standard": "我们明天晚上去看电影，好吗？",
            "cases": [
                ("明天晚上我们去看电影，好吗？", 1),
                ("我们明天晚上去看电影，怎么样？", 1),
                ("我们明天晚上去看电影吗？", 0),
                ("我们明天晚上去吃饭，好吗？", 0)
            ]
        },
        "Q42: I'm fine. How about you? (L402)": {
            "standard": "我很好。你怎么样？",
            "cases": [
                ("我挺好的。你怎么样？", 1),
                ("我很好。你呢？", 1),
                ("我不好。你好吗？", 0)
            ]
        },
        "Q43: Do you want to go play ball? (L402)": {
            "standard": "你想不想去打球？",
            "cases": [
                ("你想不想打球？", 1),
                ("你想去打球吗？", 1),
                ("你想去踢球吗？", 0)
            ]
        },
        "Q44: Never mind, I'll go find someone else. (L402)": {
            "standard": "算了，我去找别人。",
            "cases": [
                ("算了，我去找其他人。", 1),
                ("算了，我去找他。", 0)
            ]
        },
        "Q59: Your home is very big, and very beautiful too. (L501)": {
            "standard": "你们家很大,也很漂亮。",
            "cases": [
                ("你们家又大又很漂亮。", 1),
                ("你们家很大,但是不漂亮。", 0),
                ("你们家很小,也很漂亮。", 0)
            ]
        },
        "Q60: What would you like to drink? Tea or coffee? (L501)": {
            "standard": "你们想喝点儿什么?喝茶还是喝咖啡?",
            "cases": [
                ("你们想喝点儿啥?喝茶还是喝咖啡?", 1),
                ("你们想喝点儿什么?喝茶还是喝水?", 0),
                ("你们想喝点儿什么?喝咖啡还是喝水?", 0)
            ]
        },
        "Q61: I'm sorry, we don't have any cola. (L501)": {
            "standard": "对不起,我们家没有可乐。",
            "cases": [
                ("对不起,我们家没有可乐。", 1),
                ("对不起,我们家没有可乐吗？", 0),
                ("对不起,我们家没有可乐！", 1),
                ("对不起,我们家没有茶。", 0)
            ]
        },
        "Q62: We are going to see a Chinese movie tomorrow. (L501)": {
            "standard": "我们明天去看中国电影。",
            "cases": [
                ("明天我们去看中国电影。", 1),
                ("我们明天去看电影。", 0),
                ("我们明天去看美国电影。", 0),
                ("我们明天去中国看电影。", 0)
            ]
        },
        "Q25: She works at the school library. (L502)": {
            "standard": "她在学校的图书馆工作。",
            "cases": [
                ("她在学校图书馆工作。", 1),
                ("她在学校图书馆上班。", 1),
                ("她在学校的图书馆工作吗？", 0)
            ]
        },
        "Q26: Li You only drank a cup of water. (L502)": {
            "standard": "李友只喝了一杯水。",
            "cases": [
                ("李友仅仅喝了一杯水。", 1),
                ("李友只喝了一杯茶。", 0),
                ("李友喝了两杯水。", 0),
                ("李友喝了两杯茶。", 0) 
            ]
        },
        "Q27: Wang Peng and Li You didn't go home until twelve o'clock at night. (L502)": {
            "standard": "王朋和李友晚上十二点才回家。",
            "cases": [
                ("王朋李友晚上十二点才回家。", 1),
                ("王朋和李友半夜十二点才回家。", 1),
                ("王朋和李友晚上十一点才回家。", 0)
            ]
        },
        "Q28: We go to play ball at two o'clock. (L502)": {
            "standard": "我们两点去打球。",
            "cases": [
                ("两点我们去打球。", 1),
                ("我们两点钟去打球。", 1),
                ("我们两点去踢球。", 0),
                ("我们三点去打球。", 0)
            ]
        },
        "Q73: This is she. Who are you? (L601)": {
            "standard": "她就是。您是哪位？",
            "cases": [
                ("这就是她。您是哪位？", 1),
                ("她就是。您是谁？", 1),
                ("他就是。您是哪位？", 0)
            ]
        },
        "Q74: I'm sorry, I have a meeting this afternoon. (L601)": {
            "standard": "对不起,今天下午我要开会。",
            "cases": [
                ("抱歉,今天下午我要开会。", 1),
                ("对不起,今天下午我要开会。", 1),
                ("对不起,我今天下午要开会。", 1),
                ("对不起,今天下午我要开会吗？", 0),
                ("对不起,今天下午我要开会吗？", 0),
                ("对不起,明天下午我要开会！", 0)
            ]
        },
        "Q75: I won't have free time until after four o'clock tomorrow. (L601)": {
            "standard": "明天四点以后才有空儿。",
            "cases": [
                ("明天四点以后才有空儿。", 1),
                ("明天四点以后才有空。", 1),
                ("明天四点以后才有时间。", 1),
                ("明天四点以后有空儿吗？", 0)
            ]
        },
        "Q76: No problem. I'll wait for you in my office. (L601)": {
            "standard": "没问题。我在办公室等你。",
            "cases": [
                ("没问题。我在办公室等你。", 1),
                ("没问题。我在办公室等您。", 1),
                ("没事。我在办公室等你吗？", 0),
                ("没问题。我在办公室等他。", 0)
            ]
        },
        "Q35: Are you free this evening? (L602)": {
            "standard": "你今天晚上有空儿吗?",
            "cases": [
                ("你今晚空吗?", 1),
                ("你今天晚上有空儿吗?", 1),
                ("你今天晚上空不空?", 1),
                ("你明天晚上有空儿吗?", 0)
            ]
        },
        "Q36: I'll call you after I get back. (L602)": {
            "standard": "我回来以后给你打电话。",
            "cases": [
                ("等我回来给你打电话。", 1),
                ("我回来以后给你打个电话。", 1),
                ("我回来以后给你打电话吗？", 0),
                ("我回来以后给你发短信。", 0)
            ]
        },
        "Q37: You have to help me prepare for the test. (L602)": {
            "standard": "你得帮我准备考试。",
            "cases": [
                ("你得帮我准备考试", 1),
                ("你必须帮我准备考试。", 1),
                ("你得帮我准备考试吗？", 0),
                ("你得帮我准备作业。", 0)
            ]
        },
        "Q57: Li You, how did you do on last week's exam? (L701)": {
            "standard": "李友,你上个星期考试考得怎么样？",
            "cases": [
                ("李友,你上个星期考试考得怎么样？", 1),
                ("李友，你上周考试考得怎么样？", 1),
                ("李友，你下周考试考得怎么样？", 0)
            ]
        },
        "Q58: I'll practice writing characters with you from now on. How's that? (L701)": {
            "standard": "以后我跟你一起练习写字,好不好？",
            "cases": [
                ("以后我跟你一起练习写字,好不好？", 1),
                ("以后我跟你一起练习写字好吗？", 1),
                ("以后我跟你一起练习写字吗？", 0),
                ("以后我跟你一起练习写字行吗", 1)
            ]
        },
        "Q59: You teach me how to write the character 'dǒng'. (L701)": {
            "standard": "你教我怎么写“懂”字吧。",
            "cases": [
                ("你教我怎么写“懂”字好吗？", 1),
                ("我教你怎么写“懂”字吗？", 0),
                ("你教我怎么写“懂”字行吗？", 1)
            ]
        },
        "Q60: No problem. I'll help you. (L701)": {
            "standard": "没问题,我帮你。",
            "cases": [
                ("没问题,我帮你。", 1),
                ("没问题,我帮你吗？", 0),
                ("没毛病,我帮你吧。", 1)
            ]
        },
        "Q35: I didn't go to bed until four o'clock in the morning. Did you also go to bed very late? (L702)": {
            "standard": "我早上四点才睡觉，你也睡得很晚吗？",
            "cases": [
                ("我早上四点才睡觉，你也睡得很晚吗？", 1),
                ("我早上四点才睡觉，你也睡得很早吗？", 0),
            ]
        },
        "Q36: Because Wang Peng helped me practice Chinese, I finished my homework very quickly. (L702)": {
            "standard": "因为王朋帮我练习中文，所以我功课做得很快。",
            "cases": [
                ("因为王朋帮我练习中文，所以我功课做得很快。", 1),
                ("因为王朋帮我练习中文，所以我功课做得慢。", 0),
                ("王朋因为帮我练习中文，所以我功课做得很快。", 0)
            ]
        },
        "Q37: You read it very well. Did you listen to the recording last night? (L702)": {
            "standard": "你念得很好。你昨天晚上听录音了吧？",
            "cases": [
                ("你念得很好。你昨天晚上听录音吗？", 1),
                ("你读得很好。你昨天晚上听录音了吧？", 1),
                ("你念得不好。你昨天晚上听录音了没有？", 0)
            ]
        },
        "Q53: The second class was computer class. It was very difficult. (L801)": {
            "standard": "第二节是电脑课,很难。",
            "cases": [
                ("第二节是电脑课,它很难。", 1),
                ("第二节是电脑课,很难吗？", 0),
                ("第二节是电脑课,很简单。", 0)
            ]
        },
        "Q54: When I got there, she was doing her homework. (L801)": {
            "standard": "到那儿的时候,她正在做功课。",
            "cases": [
                ("我到那儿的时候,她正在做功课。", 1),
                ("到那儿的时候,她正在做作业。", 1),
                ("到那儿的时候,她正在看电视。", 0),
                ("到那儿的时候,她正在听音乐。", 0)
            ]
        },
        "Q55: Before I went to sleep, Gao Wenzhong gave me a call. (L801)": {
            "standard": "睡觉以前,高文中给我打了一个电话。",
            "cases": [
                ("我睡觉以前,高文中给我打了一个电话。", 1),
                ("睡觉前,高文中给我打了一个电话。", 1),
                ("睡觉以前,高文中给我发了一个短信。", 0),
                ("睡觉以前,高文中没有给我打电话。", 0)
            ]
        },
        "Q56: At noon, I went to the cafeteria with my classmates for lunch. (L801)": {
            "standard": "中午我和同学们一起到餐厅去吃午饭。",
            "cases": [
                ("我和同学们中午一起去餐厅吃午饭。", 1),
                ("中午我和同学们一起到餐厅吃午饭。", 1),
                ("中午我和同学们一起到餐厅去吃晚饭。", 0),
                ("中午我和同学们一起到餐厅去吃午饭吗？", 0)
            ]
        },
        "Q37: Our Chinese class is very interesting. (L802)": {
            "standard": "我们的中文课很有意思。",
            "cases": [
                ("我们的中文课很有意思。", 1),
                ("我们的中文课很有趣。", 1),
                ("我们的中文课很无聊。", 0),
                ("我们的中文课很有意思吗？", 0),
                ("我的中文课很有趣。", 0),
                ("你们的中文课很有趣。", 0)
            ]
        },
        "Q38: Next Saturday, our school has a concert. I hope you can come. (L802)": {
            "standard": "下个星期六,我们学校有一个音乐会,希望你能来。",
            "cases": [
                ("下个星期六,我们学校有一个音乐会,我希望你能来。", 1),
                ("我们学校下个星期六有一个音乐会,希望你能来。", 1),
                ("下个星期六,我们学校有一个音乐会,你能来吗？", 0)
            ]
        },
        "Q39: Li You listens to the audio recording while eating breakfast. (L802)": {
            "standard": "李友吃早饭的时候听录音。",
            "cases": [
                ("李友吃早饭的时候听录音。", 1),
                ("李友吃早饭的时候听音乐。", 0),
                ("李友吃早饭的时候看电视。", 0)
            ]
        },
        "Q40: You can't chat with him in Chinese. (L802)": {
            "standard": "你不会用中文跟他聊天。",
            "cases": [
                ("你不能用中文跟他聊天。", 1),
                ("你不会用中文跟他聊天吗？", 0),
                ("你不会用英文跟他聊天。", 0),
                ("他不会用中文跟他聊天。", 0)
            ]
        },
        "Q65: I'd like to buy a shirt. (L901)": {
            "standard": "我想买一件衬衫。",
            "cases": [
                ("我想买一件衬衫。", 1),
                ("我想买一件T恤衫。", 0),
                ("我想买一件外套。", 0),
                ("我买了一件衬衫。", 0),
                ("他想买一件衬衫", 0)
            ]
        },
        "Q66: Not too expensive, and not too cheap either. (L901)": {
            "standard": "不要太贵的，也不要太便宜的。",
            "cases": [
                ("别太贵的，也别太便宜的。", 1),
                ("不要太贵，也不要太便宜的。", 1),
                ("不要太贵的，也不要太便宜。", 1),
                ("要贵的，也要便宜的。", 0)
            ]
        },
        "Q67: How much altogether? (L901)": {
            "standard": "一共多少钱？",
            "cases": [
                ("总共多少钱？", 1),
                ("一共多少钱啊？", 1),
                ("一共多少块？", 1),
                ("一共多少？", 0)
            ]
        },
        "Q47: This pair is the same size as that one. (L902)": {
            "standard": "这双跟那双一样大。",
            "cases": [
                ("这双跟那双一样尺码。", 1),
                ("这双和那双一样大。", 1),
                ("这双跟那双一样价格。", 0),
                ("这双和那双一样小。", 1)
            ]
        },
        "Q48: Although the things in this store are inexpensive, it doesn't accept credit cards. (L902)": {
            "standard": "虽然这个商店的东西很便宜，可是不收信用卡。",
            "cases": [
                ("虽然这个商店的东西很便宜，但是它不收信用卡。", 1),
                ("虽然这个商店的东西很便宜，可是它收信用卡。", 0),
                ("虽然这个商店的东西很贵，可是不收信用卡。", 0)
            ]
        },
        "Q49: The grammar of Lesson 9 is as difficult as the grammar of Lesson 8. (L902)": {
            "standard": "第九课的语法跟第八课的语法一样难。",
            "cases": [
                ("第九课的语法跟第八课的一样难。", 1),
                ("第九课的语法跟第八课的语法一样难吗？", 0),
                ("第九课的语法跟第八课的语法一样简单。", 0)
            ]
        },
        "Q50: Although this pair of pants is inexpensive, the length is not suitable. (L902)": {
            "standard": "虽然这条裤子很便宜，可是长短不合适。",
            "cases": [
                ("虽然这条裤子便宜，但是长短不合适。", 1),
                ("虽然这条裤子很贵，但是长短不合适。", 0),
                ("虽然这条裤子很便宜，但是长短合适。", 0)
            ]
        },
        "Q67: How are you getting to the airport? (L1001)": {
            "standard": "你怎么去机场?",
            "cases": [
                ("你怎么去机场？", 1),
                ("你怎么去飞机场？", 1),
                ("你怎么去火车站？", 0),
                ("你怎么去汽车站？", 0),
                ("他怎么去机场？", 0)
            ]
        },
        "Q68: Taxis are too expensive. I'll drive you there. (L1001)": {
            "standard": "出租汽车太贵,我开车送你去吧。",
            "cases": [
                ("出租汽车太贵了,我开车送你去吧。", 1),
                ("出租汽车太贵,我开车送你去吗？", 0),
                ("出租汽车太贵,我开车送他去吧。", 0)
            ]
        },
        "Q69: We'd better take a taxi instead. (L1001)": {
            "standard": "我们还是打车去吧。",
            "cases": [
                ("我们最好打车去吧。", 1),
                ("我们还是坐出租车去吧。", 1),
                ("我们还是坐公交车去吧。", 0),
                ("你们还是打车去吧。", 0)
            ]
        },
        "Q70: You'd better major in computer science instead. (L1001)": {
            "standard": "你还是学计算机专业吧。",
            "cases": [
                ("你最好学计算机专业吧。", 1),
                ("你还是学计算机科学专业吧。", 1),
                ("你还是学历史专业吧。", 0),
                ("我还是学计算机专业吧。", 0)
            ]
        },
        "Q43: I drive on the highway. (L1002)": {
            "standard": "我在高速公路上开车。",
            "cases": [
                ("我在高速公路上开车。", 1),
                ("我在高速公路上开车吗？", 0),
                ("我在高速公路上开车！", 1),
                ("我在城市里开车。", 0),
                ("你在高速公路上开车。", 0)
            ]
        },
        "Q44: Lawyer Wang takes a plane to New York. (L1002)": {
            "standard": "王律师坐飞机去纽约。",
            "cases": [
                ("王律师坐飞机去纽约。", 1),
                ("王律师坐飞机去美国。", 0),
                ("王律师坐飞机去北京。", 0),
                ("李律师坐飞机去纽约。", 0)
            ]
        },
        "Q45: Bai Ying'ai's shoes are very pretty. (L1002)": {
            "standard": "白英爱的鞋很漂亮。",
            "cases": [
                ("白英爱的鞋很漂亮。", 1),
                ("白英爱的鞋很漂亮吗？", 0),
                ("白英爱的脚很漂亮！", 0),
                ("白英爱的鞋很丑。", 0)
            ]
        },
    }
}

