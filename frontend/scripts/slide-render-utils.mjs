import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const manifestPath = fileURLToPath(new URL('../../backend/content_builder/core/pipeline_manifest.json', import.meta.url));
const pipelines = JSON.parse(fs.readFileSync(manifestPath, 'utf8')).pipelines;

export { STATIC_SLIDE_VERSION, SUPPORTED_TEMPLATES, staticSegment } from '../src/videoTemplates/explanation/staticSlideData.js';

export function renderPropsForSegment(composition, segment) {
    const inputProps = { segment };
    // renderStill serializes composition.props separately from inputProps.
    // Both must change on every page when the selected composition is reused.
    return { composition: { ...composition, props: inputProps }, inputProps };
}

export function artifactRootFor(projectRoot, pipeline) {
    return artifactRootsFor(projectRoot, pipeline)[0];
}

export function artifactRootsFor(projectRoot, pipeline) {
    const id = String(pipeline).trim().toLowerCase();
    const entry = pipelines.find((item) => item.pipeline_id === id || item.aliases?.includes(id));
    if (!entry) throw new Error(`Unknown content pipeline: ${pipeline}`);
    return [entry.artifact_relative_path, entry.legacy_artifact_relative_path,
        ...(entry.pipeline_id === 'integrated_chinese' ? ['content_builder/artifacts'] : [])]
        .filter(Boolean).map((relative) => path.join(projectRoot, 'backend', ...relative.split('/')));
}
