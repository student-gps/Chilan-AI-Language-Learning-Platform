import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
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

const result = spawnSync(
    executable,
    args,
    {
        cwd: frontendDir,
        stdio: 'inherit',
        shell: false,
    }
);

if (result.error) {
    console.error('❌ Remotion 渲染进程启动失败:', result.error);
    process.exit(1);
}

if (result.status !== 0) {
    console.error(`❌ Remotion 渲染失败，退出码: ${result.status}`);
    process.exit(result.status ?? 1);
}

console.log(`✅ 渲染完成: ${outputFile}`);
