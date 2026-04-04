import os
import time
from typing import Any

import requests


class Task4ADramatizationRenderer:
    BASE_URL = "https://api.lumalabs.ai/dream-machine/v1/generations"

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "ray-flash-2",
        resolution: str = "720p",
        duration: str = "5s",
        aspect_ratio: str = "16:9",
        poll_interval_seconds: int = 3,
        request_timeout_seconds: int = 60,
    ):
        self.api_key = (api_key or os.getenv("LUMA_API_KEY") or os.getenv("LUMAAI_API_KEY") or "").strip()
        self.model = model
        self.resolution = resolution
        self.duration = duration
        self.aspect_ratio = aspect_ratio
        self.poll_interval_seconds = poll_interval_seconds
        self.request_timeout_seconds = request_timeout_seconds

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ValueError("LUMA_API_KEY 未配置，无法调用 Luma API。")
        return {
            "accept": "application/json",
            "authorization": f"Bearer {self.api_key}",
            "content-type": "application/json",
        }

    def _clean_join(self, parts: list[str]) -> str:
        return " ".join(part.strip() for part in parts if isinstance(part, str) and part.strip())

    def _build_prompt(self, global_config: dict, scene: dict) -> str:
        global_config = global_config if isinstance(global_config, dict) else {}
        scene = scene if isinstance(scene, dict) else {}

        visual_style = (global_config.get("visual_style") or "").strip()
        setting_summary = (global_config.get("setting_summary_en") or "").strip()
        setting_en = (scene.get("setting_en") or "").strip()
        shot_type = (scene.get("shot_type") or "").strip()
        camera_movement = (scene.get("camera_movement") or "").strip()
        video_prompt_en = (scene.get("video_prompt_en") or "").strip()

        characters = scene.get("characters_on_screen", [])
        character_text = ", ".join(
            item.strip() for item in characters if isinstance(item, str) and item.strip()
        )

        prompt_parts = [
            f"Visual style: {visual_style}." if visual_style else "",
            f"Lesson setting: {setting_summary}." if setting_summary else "",
            f"Scene setting: {setting_en}." if setting_en else "",
            f"Shot type: {shot_type}." if shot_type else "",
            f"Camera motion: {camera_movement}." if camera_movement else "",
            f"Characters on screen: {character_text}." if character_text else "",
            video_prompt_en,
        ]
        return self._clean_join(prompt_parts)

    def _build_payload(self, global_config: dict, scene: dict) -> dict[str, Any]:
        return {
            "prompt": self._build_prompt(global_config, scene),
            "model": self.model,
            "resolution": self.resolution,
            "duration": self.duration,
            "aspect_ratio": self.aspect_ratio,
        }

    def create_generation(self, global_config: dict, scene: dict) -> dict[str, Any]:
        payload = self._build_payload(global_config, scene)
        response = requests.post(
            self.BASE_URL,
            headers=self._headers(),
            json=payload,
            timeout=self.request_timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def get_generation(self, generation_id: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.BASE_URL}/{generation_id}",
            headers=self._headers(),
            timeout=self.request_timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def wait_for_generation(self, generation_id: str, timeout_seconds: int = 600) -> dict[str, Any]:
        started = time.time()
        while True:
            generation = self.get_generation(generation_id)
            state = (generation.get("state") or "").strip().lower()

            if state == "completed":
                return generation
            if state == "failed":
                failure_reason = generation.get("failure_reason") or "unknown failure"
                raise RuntimeError(f"Luma generation failed: {failure_reason}")
            if time.time() - started > timeout_seconds:
                raise TimeoutError(f"Luma generation polling timed out after {timeout_seconds} seconds.")

            print(f"    ... scene generation {generation_id} 当前状态: {state or 'unknown'}")
            time.sleep(self.poll_interval_seconds)

    def _extract_asset_url(self, generation: dict, asset_name: str) -> str:
        assets = generation.get("assets", {}) if isinstance(generation, dict) else {}
        if not isinstance(assets, dict):
            return ""
        value = assets.get(asset_name)
        return value.strip() if isinstance(value, str) else ""

    def _build_artifact(self, scene: dict, payload: dict, generation: dict, status: str) -> dict[str, Any]:
        generation_id = (generation.get("id") or "").strip() if isinstance(generation, dict) else ""
        return {
            "scene_id": scene.get("scene_id"),
            "source_line_refs": scene.get("source_line_refs", []) if isinstance(scene.get("source_line_refs"), list) else [],
            "provider": "luma",
            "model": payload.get("model", self.model),
            "status": status,
            "generation_id": generation_id,
            "request_payload": payload,
            "video_url": self._extract_asset_url(generation, "video"),
            "thumbnail_url": self._extract_asset_url(generation, "image"),
            "duration_seconds": scene.get("estimated_duration_seconds"),
        }

    def render_scene(self, global_config: dict, scene: dict, wait_for_result: bool = False) -> dict[str, Any]:
        created = self.create_generation(global_config, scene)
        generation_id = created.get("id")
        payload = self._build_payload(global_config, scene)

        if not wait_for_result:
            return self._build_artifact(scene, payload, created, status=(created.get("state") or "submitted"))

        completed = self.wait_for_generation(generation_id)
        return self._build_artifact(scene, payload, completed, status=(completed.get("state") or "completed"))

    def render_video_plan(
        self,
        video_plan: dict,
        scene_limit: int | None = None,
        wait_for_result: bool = False,
    ) -> dict[str, Any]:
        video_plan = video_plan if isinstance(video_plan, dict) else {}
        dramatization = video_plan.get("dramatization", {}) if isinstance(video_plan.get("dramatization"), dict) else {}
        global_config = dramatization.get("global_config", {}) if isinstance(dramatization.get("global_config"), dict) else {}
        scenes = dramatization.get("scenes", []) if isinstance(dramatization.get("scenes"), list) else []

        if scene_limit is not None:
            scenes = scenes[:scene_limit]

        clips = []
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            scene_id = scene.get("scene_id")
            print(f"  ▶️ [Task 4A] 正在提交 scene {scene_id} 到 Luma...")
            artifact = self.render_scene(global_config, scene, wait_for_result=wait_for_result)
            clips.append(artifact)
            print(f"  ✨ [Task 4A] scene {scene_id} 已提交，状态: {artifact.get('status')}")

        lesson_plan = video_plan.get("lesson_video_plan", {}) if isinstance(video_plan.get("lesson_video_plan"), dict) else {}
        return {
            "render_artifacts": {
                "lesson_id": lesson_plan.get("lesson_id"),
                "lesson_title": lesson_plan.get("lesson_title", ""),
                "dramatization_clips": clips,
                "provider": "luma",
                "model": self.model,
                "resolution": self.resolution,
                "duration": self.duration,
                "aspect_ratio": self.aspect_ratio,
            }
        }
