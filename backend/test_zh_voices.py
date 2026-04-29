import requests, os, subprocess
from pathlib import Path

for line in Path('.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

key    = os.environ['TTS_AZURE_KEY']
region = os.environ.get('TTS_AZURE_REGION', 'eastus')

def synth(ssml, out):
    resp = requests.post(
        f'https://{region}.tts.speech.microsoft.com/cognitiveservices/v1',
        headers={'Ocp-Apim-Subscription-Key': key, 'Content-Type': 'application/ssml+xml',
                 'X-Microsoft-OutputFormat': 'audio-24khz-96kbitrate-mono-mp3'},
        data=ssml.encode('utf-8'), timeout=30)
    resp.raise_for_status()
    Path(out).write_bytes(resp.content)

zh_text = "你好，请问，你贵姓？我姓李，你呢？"

zh_voices = [
    ("zh-CN-XiaoxiaoNeural",  "xiaoiao"),
    ("zh-CN-XiaoyiNeural",    "xiaoyi"),
    ("zh-CN-XiaohanNeural",   "xiaohan"),
    ("zh-CN-XiaochenNeural",  "xiaochen"),
    ("zh-CN-XiaoruiNeural",   "xiaorui"),
]

# French context sentence (Denise)
fr_ssml = (
    '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="fr-FR">'
    '<voice name="fr-FR-DeniseNeural">'
    "Commençons par la salutation la plus essentielle en chinois."
    '</voice></speak>'
)
synth(fr_ssml, 'cmp_fr_denise.mp3')
print('✅ cmp_fr_denise.mp3')

for voice, tag in zh_voices:
    zh_ssml = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">'
        f'<voice name="{voice}">{zh_text}</voice></speak>'
    )
    zh_file = f'cmp_zh_{tag}.mp3'
    synth(zh_ssml, zh_file)

    # Concat: FR sentence → ZH phrase → FR sentence
    with open('_concat.txt', 'w') as f:
        f.write(f"file 'cmp_fr_denise.mp3'\nfile '{zh_file}'\nfile 'cmp_fr_denise.mp3'\n")
    out = f'cmp_full_{tag}.mp3'
    subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', '_concat.txt',
                    '-c:a', 'libmp3lame', '-q:a', '4', out],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f'✅ cmp_full_{tag}.mp3  ({voice})')

Path('_concat.txt').unlink(missing_ok=True)
print('\n听每个 cmp_full_*.mp3，选你觉得切换最自然的中文声音。')
