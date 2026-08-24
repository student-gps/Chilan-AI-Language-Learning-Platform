import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import process from 'node:process';

const currentFilePath = fileURLToPath(import.meta.url);
const frontendDir = path.resolve(path.dirname(currentFilePath), '..');
const projectRoot = path.resolve(frontendDir, '..');
const pipelineManifestPath = path.join(projectRoot, 'backend', 'content_builder', 'core', 'pipeline_manifest.json');

function loadPipelineManifest() {
    const payload = JSON.parse(fs.readFileSync(pipelineManifestPath, 'utf-8'));
    return Array.isArray(payload?.pipelines) ? payload.pipelines : [];
}

function buildPipelineMaps() {
    const currentArtifactRootByPipeline = {};
    const legacyArtifactRootByPipeline = {};
    const aliasToPipelineId = {};

    for (const pipeline of loadPipelineManifest()) {
        const pipelineId = String(pipeline.pipeline_id || '').trim();
        if (!pipelineId) continue;
        const artifactRelativePath = String(pipeline.artifact_relative_path || '').trim();
        if (artifactRelativePath) {
            currentArtifactRootByPipeline[pipelineId] = path.join(projectRoot, 'backend', ...artifactRelativePath.split('/'));
        }
        const legacyRelativePath = String(pipeline.legacy_artifact_relative_path || '').trim();
        if (legacyRelativePath) {
            legacyArtifactRootByPipeline[pipelineId] = path.join(projectRoot, 'backend', ...legacyRelativePath.split('/'));
        }
        aliasToPipelineId[pipelineId.toLowerCase()] = pipelineId;
        for (const alias of Array.isArray(pipeline.aliases) ? pipeline.aliases : []) {
            aliasToPipelineId[String(alias).trim().toLowerCase()] = pipelineId;
        }
    }

    return { currentArtifactRootByPipeline, legacyArtifactRootByPipeline, aliasToPipelineId };
}

const { currentArtifactRootByPipeline, legacyArtifactRootByPipeline, aliasToPipelineId } = buildPipelineMaps();

const lessonId = process.argv[2] || '101';
const lang = process.argv[3] || 'en';
const pipeline = (process.argv[4] || 'integrated_chinese').trim();
const sourceJsonArg = process.argv[5] || '';
const onlySlideArg = Number.parseInt(process.argv[6] || '', 10);
const onlySlideIndex = Number.isFinite(onlySlideArg) && onlySlideArg > 0 ? onlySlideArg : null;
const langSuffix = lang !== 'en' ? `_${lang}` : '';
const canonicalPipelineId = aliasToPipelineId[pipeline.toLowerCase()] || pipeline;
const legacyArtifactsDir = path.join(projectRoot, 'backend', 'content_builder', 'artifacts');
const preferredArtifactRoot = currentArtifactRootByPipeline[canonicalPipelineId] || legacyArtifactRootByPipeline[canonicalPipelineId] || path.join(legacyArtifactsDir, canonicalPipelineId);

const candidateArtifactRoots = [
    preferredArtifactRoot,
    legacyArtifactRootByPipeline[canonicalPipelineId],
    ...Object.values(currentArtifactRootByPipeline),
    ...Object.values(legacyArtifactRootByPipeline),
    legacyArtifactsDir,
].filter(Boolean).filter((item, index, arr) => arr.indexOf(item) === index);

const candidateJsonPaths = sourceJsonArg
    ? [path.resolve(sourceJsonArg)]
    : candidateArtifactRoots.flatMap((artifactRoot) => [
        path.join(artifactRoot, 'output_json', lang, `lesson${lessonId}_data${langSuffix}.json`),
        path.join(artifactRoot, 'output_json', lang, `lesson${lessonId}_data.json`),
        path.join(artifactRoot, 'synced_json', lang, `lesson${lessonId}_data${langSuffix}.json`),
        path.join(artifactRoot, 'synced_json', lang, `lesson${lessonId}_data.json`),
    ]);

const sourceJsonPath = candidateJsonPaths.find((candidate) => fs.existsSync(candidate));

if (!sourceJsonPath) {
    console.error(`未找到 lesson${lessonId} 的数据文件，已尝试:\n${candidateJsonPaths.join('\n')}`);
    process.exit(1);
}

const artifactRoot = candidateArtifactRoots.find((root) => sourceJsonPath.startsWith(root)) || preferredArtifactRoot;
const raw = JSON.parse(fs.readFileSync(sourceJsonPath, 'utf-8'));
const rawRenderPlan = raw?.video_render_plan?.explanation;

function preferredNarrationText(segment = {}) {
    const track = segment?.narration_track || {};
    return track[`subtitle_${lang}`]
        || track.script
        || track.subtitle_zh
        || track.subtitle_en
        || '';
}

const renderPlan = rawRenderPlan && Array.isArray(rawRenderPlan.segments)
    ? {
        ...rawRenderPlan,
        segments: rawRenderPlan.segments.map((segment) => {
            const { sentence_texts, sentence_timings_seconds, narration_track, ...rest } = segment || {};
            return {
                ...rest,
                narration_track: {
                    ...(narration_track || {}),
                    script: preferredNarrationText(segment),
                },
            };
        }),
    }
    : rawRenderPlan;

if (!renderPlan || !Array.isArray(renderPlan?.segments) || renderPlan.segments.length === 0) {
    console.error(`lesson${lessonId} 缺少 video_render_plan.explanation.segments，无法渲染。`);
    process.exit(1);
}

const generatedDir = path.join(frontendDir, 'remotion', 'generated');
fs.mkdirSync(generatedDir, { recursive: true });
const renderToken = `${lessonId}_${lang}_${process.pid}_${Date.now()}`.replace(/[^a-zA-Z0-9_-]/g, '_');
const generatedModulePath = path.join(generatedDir, `explanationRenderPlan_${renderToken}.js`);
const generatedEntryPath = path.join(generatedDir, `explanationSlideEntry_${renderToken}.jsx`);
const moduleSource = `const explanationRenderPlan = ${JSON.stringify(renderPlan, null, 2)};\n\nexport default explanationRenderPlan;\n`;
fs.writeFileSync(generatedModulePath, moduleSource, 'utf-8');

const totalDurationSeconds = Number(renderPlan?.timeline?.total_duration_seconds) || 10;
const durationInFrames = Math.max(30, Math.ceil(totalDurationSeconds * 30));
const entrySource = `import React from 'react';
import { Composition, registerRoot } from 'remotion';
import ExplanationLessonVideo from '../ExplanationLessonVideo';
import explanationRenderPlan from './${path.basename(generatedModulePath)}';

const FPS = 30;
const WIDTH = 1920;
const HEIGHT = 1080;

function RemotionRoot() {
    return (
        <Composition
            id="ExplanationLessonSlide"
            component={ExplanationLessonVideo}
            durationInFrames={${durationInFrames}}
            fps={FPS}
            width={WIDTH}
            height={HEIGHT}
            defaultProps={{
                renderPlan: explanationRenderPlan,
                // Static deck images stay on screen while the player advances
                // caption_cues, so baking one cue into the image causes the two
                // subtitle surfaces to diverge as soon as narration advances.
                showSubtitleBar: false,
            }}
        />
    );
}

registerRoot(RemotionRoot);
`;
fs.writeFileSync(generatedEntryPath, entrySource, 'utf-8');

const cleanupGeneratedFiles = () => {
    for (const filePath of [generatedModulePath, generatedEntryPath]) {
        try {
            if (fs.existsSync(filePath)) {
                fs.unlinkSync(filePath);
            }
        } catch {
            // Best-effort cleanup only; stale generated files do not affect render correctness.
        }
    }
};
process.on('exit', cleanupGeneratedFiles);

const outputDir = path.join(artifactRoot, 'output_slides', lang, `lesson${lessonId}`);
fs.mkdirSync(outputDir, { recursive: true });

const generatedEntryForRemotion = path.relative(frontendDir, generatedEntryPath).replace(/\\/g, '/');

console.log(`🖼️ 已生成 Remotion 输入数据: ${generatedModulePath}`);
console.log(`🖼️ 已生成独立 Remotion 入口: ${generatedEntryPath}`);
console.log(`🖼️ 使用内容产物目录: ${artifactRoot}`);
console.log(`🖼️ 开始导出 lesson${lessonId} 静态教学幻灯片 -> ${outputDir}`);

const remotionExecutable = process.platform === 'win32'
    ? path.join(frontendDir, 'node_modules', '.bin', 'remotion.cmd')
    : path.join(frontendDir, 'node_modules', '.bin', 'remotion');

const hasLocalRemotion = fs.existsSync(remotionExecutable);

const runStill = (frame, outputFile) => new Promise((resolve, reject) => {
    let executable;
    let args;

    if (process.platform === 'win32') {
        executable = 'cmd.exe';
        args = hasLocalRemotion
            ? ['/c', remotionExecutable, 'still', generatedEntryForRemotion, 'ExplanationLessonSlide', outputFile, '--frame', String(frame)]
            : ['/c', 'npx.cmd', 'remotion', 'still', generatedEntryForRemotion, 'ExplanationLessonSlide', outputFile, '--frame', String(frame)];
    } else {
        executable = hasLocalRemotion ? remotionExecutable : 'npx';
        args = hasLocalRemotion
            ? ['still', generatedEntryForRemotion, 'ExplanationLessonSlide', outputFile, '--frame', String(frame)]
            : ['remotion', 'still', generatedEntryForRemotion, 'ExplanationLessonSlide', outputFile, '--frame', String(frame)];
    }

    const child = spawn(executable, args, {
        cwd: frontendDir,
        stdio: ['ignore', 'pipe', 'pipe'],
        shell: false,
    });

    let stderr = '';
    child.stdout.on('data', (chunk) => process.stdout.write(chunk));
    child.stderr.on('data', (chunk) => {
        stderr += chunk.toString();
        process.stderr.write(chunk);
    });
    child.on('error', reject);
    child.on('close', (code) => {
        if (code === 0) {
            resolve();
        } else {
            reject(new Error(`Remotion still 渲染失败，退出码: ${code}\n${stderr}`));
        }
    });
});

const FPS = 30;
const outputs = [];
const slideIndexes = onlySlideIndex
    ? [onlySlideIndex - 1].filter((index) => index >= 0 && index < renderPlan.segments.length)
    : renderPlan.segments.map((_, index) => index);

if (onlySlideIndex && slideIndexes.length === 0) {
    console.error(`slide ${onlySlideIndex} 超出范围，当前共 ${renderPlan.segments.length} 页。`);
    process.exit(1);
}

for (const i of slideIndexes) {
    const segment = renderPlan.segments[i];
    const startFrame = Math.round((Number(segment?.start_time_seconds) || 0) * FPS);
    const settleFrames = 18;
    const frame = startFrame + settleFrames;
    const outputFile = path.join(outputDir, `slide_${String(i + 1).padStart(3, '0')}.png`);
    console.log(`\n🖼️  [${i + 1}/${renderPlan.segments.length}] frame ${frame} -> ${path.basename(outputFile)}`);
    await runStill(frame, outputFile);
    outputs.push(outputFile);
}

console.log(`\n✅ 静态幻灯片导出完成，共 ${outputs.length} 页。`);
cleanupGeneratedFiles();
