import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import process from 'node:process';

const currentFilePath = fileURLToPath(import.meta.url);
const frontendDir = path.resolve(path.dirname(currentFilePath), '..');
const projectRoot = path.resolve(frontendDir, '..');
const lessonId = process.argv[2] || '101';
const lang = process.argv[3] || 'en';
const pipeline = (process.argv[4] || 'integrated_chinese').trim();
const langSuffix = lang !== 'en' ? `_${lang}` : '';

const artifactsDir = path.join(projectRoot, 'backend', 'content_builder', 'artifacts');
const artifactRootByPipeline = {
    integrated_chinese: path.join(artifactsDir, 'integrated_chinese'),
    'integrated-chinese': path.join(artifactsDir, 'integrated_chinese'),
    zh: path.join(artifactsDir, 'integrated_chinese'),
    new_concept_english: path.join(artifactsDir, 'new_concept_english'),
    'new-concept-english': path.join(artifactsDir, 'new_concept_english'),
    nce: path.join(artifactsDir, 'new_concept_english'),
};
const preferredArtifactRoot = artifactRootByPipeline[pipeline] || path.join(artifactsDir, pipeline);

const candidateArtifactRoots = [
    preferredArtifactRoot,
    path.join(artifactsDir, 'integrated_chinese'),
    path.join(artifactsDir, 'new_concept_english'),
    artifactsDir,
].filter((item, index, arr) => arr.indexOf(item) === index);

const candidateJsonPaths = candidateArtifactRoots.flatMap((artifactRoot) => [
    path.join(artifactRoot, 'output_json', lang, `lesson${lessonId}_data${langSuffix}.json`),
    path.join(artifactRoot, 'synced_json', lang, `lesson${lessonId}_data${langSuffix}.json`),
]);
const sourceJsonPath = candidateJsonPaths.find((candidate) => fs.existsSync(candidate));

if (!sourceJsonPath) {
    console.error(`未找到 lesson${lessonId} 的数据文件，已尝试:\n${candidateJsonPaths.join('\n')}`);
    process.exit(1);
}

const artifactRoot = candidateArtifactRoots.find((root) => sourceJsonPath.startsWith(root)) || preferredArtifactRoot;

const raw = JSON.parse(fs.readFileSync(sourceJsonPath, 'utf-8'));
const renderPlan = raw?.video_render_plan?.explanation;

if (!renderPlan || !Array.isArray(renderPlan?.segments) || renderPlan.segments.length === 0) {
    console.error(`lesson${lessonId} 缺少 video_render_plan.explanation.segments，无法渲染。`);
    process.exit(1);
}

const generatedModulePath = path.join(frontendDir, 'remotion', 'generated', 'explanationRenderPlan.js');
const moduleSource = `const explanationRenderPlan = ${JSON.stringify(renderPlan, null, 2)};\n\nexport default explanationRenderPlan;\n`;
fs.writeFileSync(generatedModulePath, moduleSource, 'utf-8');

const outputDir = path.join(artifactRoot, 'output_video');
fs.mkdirSync(outputDir, { recursive: true });
const outputFile = path.join(outputDir, `lesson${lessonId}_explanation.mp4`);

console.log(`🎬 已生成 Remotion 输入数据: ${generatedModulePath}`);
console.log(`🎬 使用内容产物目录: ${artifactRoot}`);
console.log(`🎬 开始渲染 lesson${lessonId} 教学讲解视频 -> ${outputFile}`);

const remotionExecutable = process.platform === 'win32'
    ? path.join(frontendDir, 'node_modules', '.bin', 'remotion.cmd')
    : path.join(frontendDir, 'node_modules', '.bin', 'remotion');

const hasLocalRemotion = fs.existsSync(remotionExecutable);

let executable;
let args;

if (process.platform === 'win32') {
    executable = 'cmd.exe';
    args = hasLocalRemotion
        ? ['/c', remotionExecutable, 'render', 'remotion/index.jsx', 'ExplanationLessonVideo', outputFile]
        : ['/c', 'npx.cmd', 'remotion', 'render', 'remotion/index.jsx', 'ExplanationLessonVideo', outputFile];
} else {
    executable = hasLocalRemotion ? remotionExecutable : 'npx';
    args = hasLocalRemotion
        ? ['render', 'remotion/index.jsx', 'ExplanationLessonVideo', outputFile]
        : ['remotion', 'render', 'remotion/index.jsx', 'ExplanationLessonVideo', outputFile];
}

const stripAnsi = (value) => value.replace(/\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])/g, '');
const progressRe = /(?:Rendering frames|Rendered)\s+.*?(\d+)\/(\d+)/;
let lastProgressPercent = -1;
let lastProgressAt = 0;

const renderBar = (current, total) => {
    const width = 26;
    const ratio = total > 0 ? Math.min(1, current / total) : 0;
    const done = Math.round(ratio * width);
    return `${'█'.repeat(done)}${'░'.repeat(width - done)} ${current}/${total} ${Math.round(ratio * 100)}%`;
};

const printProgress = (current, total, done = false) => {
    const percent = total > 0 ? Math.floor((current / total) * 100) : 0;
    const now = Date.now();
    const shouldPrint = (
        done ||
        lastProgressPercent < 0 ||
        percent >= lastProgressPercent + 5 ||
        now - lastProgressAt > 5000
    );
    if (!shouldPrint) return;
    lastProgressPercent = percent;
    lastProgressAt = now;
    const line = `🎞️ Remotion frames ${renderBar(current, total)}`;
    process.stdout.write(`\r${line.padEnd(90, ' ')}`);
    if (done) process.stdout.write('\n');
};

const handleRemotionOutput = (chunk) => {
    const raw = chunk.toString();
    for (const part of raw.split(/[\r\n]+/)) {
        const clean = stripAnsi(part).trim();
        if (!clean) continue;
        const progress = clean.match(progressRe);
        if (progress) {
            printProgress(Number(progress[1]), Number(progress[2]));
            continue;
        }
        if (/time remaining:/i.test(clean)) {
            continue;
        }
        console.log(clean);
    }
};

const runRemotion = () => new Promise((resolve, reject) => {
    const child = spawn(executable, args, {
        cwd: frontendDir,
        stdio: ['ignore', 'pipe', 'pipe'],
        shell: false,
    });

    child.stdout.on('data', handleRemotionOutput);
    child.stderr.on('data', handleRemotionOutput);
    child.on('error', reject);
    child.on('close', (code) => {
        if (lastProgressPercent >= 0) {
            process.stdout.write('\n');
        }
        if (code === 0) {
            resolve();
        } else {
            reject(new Error(`Remotion 渲染失败，退出码: ${code}`));
        }
    });
});

try {
    await runRemotion();
} catch (error) {
    console.error('❌ Remotion 渲染进程失败:', error);
    process.exit(1);
}

console.log(`✅ 渲染完成: ${outputFile}`);
