try:
    from content_builder.pipelines.integrated_chinese.tasks.video_director import *  # noqa: F401,F403
except ImportError:
    from pipelines.integrated_chinese.tasks.video_director import *  # noqa: F401,F403

