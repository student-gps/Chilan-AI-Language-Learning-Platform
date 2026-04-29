try:
    from content_builder.pipelines.integrated_chinese.tasks.narration_audio import *  # noqa: F401,F403
except ImportError:
    from pipelines.integrated_chinese.tasks.narration_audio import *  # noqa: F401,F403

