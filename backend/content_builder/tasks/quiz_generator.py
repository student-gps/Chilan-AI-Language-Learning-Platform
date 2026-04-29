try:
    from content_builder.pipelines.integrated_chinese.tasks.quiz_generator import *  # noqa: F401,F403
except ImportError:
    from pipelines.integrated_chinese.tasks.quiz_generator import *  # noqa: F401,F403

