import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { bundle } from '@remotion/bundler';
import { openBrowser, renderStill, selectComposition } from '@remotion/renderer';
import { artifactRootsFor, renderPropsForSegment, staticSegment, STATIC_SLIDE_VERSION } from './slide-render-utils.mjs';

const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const projectRoot = path.resolve(frontendDir, '..');
const lessonId = process.argv[2] || '101';
const lang = process.argv[3] || 'en';
const pipeline = process.argv[4] || 'integrated_chinese';
const sourceJsonArg = process.argv[5];
const onlySlide = !process.argv[6] ? null : Number(process.argv[6]);
const outputOverride = process.argv[7];
const artifactRoots = artifactRootsFor(projectRoot, pipeline);
const suffix = lang !== 'en' ? `_${lang}` : '';
const candidates = sourceJsonArg ? [path.resolve(sourceJsonArg)] : artifactRoots.flatMap((root) =>
    ['output_json', 'synced_json'].flatMap((folder) => [
        path.join(root, folder, lang, `lesson${lessonId}_data${suffix}.json`),
        path.join(root, folder, lang, `lesson${lessonId}_data.json`),
    ]));
const sourceJsonPath = candidates.find((candidate) => fs.existsSync(candidate));
if (!sourceJsonPath) throw new Error(`Lesson JSON not found:\n${candidates.join('\n')}`);
const artifactRoot = artifactRoots.find((root) => sourceJsonPath.startsWith(`${root}${path.sep}`)) || artifactRoots[0];
const raw = JSON.parse(fs.readFileSync(sourceJsonPath, 'utf8'));
const segments = raw?.video_render_plan?.explanation?.segments;
if (!Array.isArray(segments) || !segments.length) throw new Error('Explanation segments are empty.');
if (onlySlide !== null && (!Number.isInteger(onlySlide) || onlySlide < 1 || onlySlide > segments.length)) {
    throw new Error(`Slide index must be 1..${segments.length}.`);
}
const boards = segments.map(staticSegment);
const indexes = onlySlide === null ? boards.map((_, i) => i) : [onlySlide - 1];
const outputDir = outputOverride ? path.resolve(outputOverride) : path.join(artifactRoot, 'output_slides', lang, `lesson${lessonId}`);
fs.mkdirSync(outputDir, { recursive: true });
const generatedDir = path.join(frontendDir, 'remotion', 'generated');
fs.mkdirSync(generatedDir, { recursive: true });
const entryPath = path.join(generatedDir, `staticSlide_${process.pid}_${Date.now()}.jsx`);
const bundleDir = fs.mkdtempSync(path.join(os.tmpdir(), 'chilan-slides-'));
fs.writeFileSync(entryPath, `import React from 'react';
import { Composition, registerRoot } from 'remotion';
import ExplanationLessonSlide from '../ExplanationLessonSlide';
const Root = () => <Composition id="TeachingSlide" component={ExplanationLessonSlide}
    width={1920} height={1080} fps={30} durationInFrames={1} defaultProps={{ segment: {} }} />;
registerRoot(Root);
`, 'utf8');
let browser;
try {
    // Build once and reuse one browser for the whole lesson. Still images have
    // no animation, no narration, and no dependency on a sampled video frame.
    console.log(`Rendering ${indexes.length} caption-free slide(s), recipe v${STATIC_SLIDE_VERSION}.`);
    const serveUrl = await bundle({ entryPoint: entryPath, outDir: bundleDir, publicDir: null });
    browser = await openBrowser('chrome');
    const composition = await selectComposition({ serveUrl, id: 'TeachingSlide', inputProps: { segment: boards[0] }, puppeteerInstance: browser });
    for (const i of indexes) {
        const output = path.join(outputDir, `slide_${String(i + 1).padStart(3, '0')}.png`);
        await renderStill({ serveUrl, ...renderPropsForSegment(composition, boards[i]),
            output, frame: 0, imageFormat: 'png', puppeteerInstance: browser });
        console.log(`[${i + 1}/${boards.length}] ${output}`);
    }
} finally {
    if (browser) await browser.close({ silent: true });
    fs.rmSync(entryPath, { force: true });
    const resolvedBundle = path.resolve(bundleDir);
    if (path.dirname(resolvedBundle) !== path.resolve(os.tmpdir()) || !path.basename(resolvedBundle).startsWith('chilan-slides-')) {
        throw new Error('Unexpected temporary bundle path.');
    }
    fs.rmSync(resolvedBundle, { recursive: true, force: true });
}
