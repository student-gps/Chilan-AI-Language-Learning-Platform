import argparse
import json
from pathlib import Path


PUNCTUATION_MAP = {
    "，": ",",
    "。": ".",
    "？": "?",
    "！": "!",
    "：": ":",
    "；": ";",
    "、": ",",
    "（": "(",
    "）": ")",
    "“": "\"",
    "”": "\"",
    "‘": "'",
    "’": "'",
}


def _capitalize_first_alpha(text: str) -> str:
    chars = list(text)
    for index, char in enumerate(chars):
        if char.isalpha():
            chars[index] = char.upper()
            break
    return "".join(chars)


def _normalize_words(words: list) -> list:
    return [
        {
            "cn": (token.get("cn") or "").strip(),
            "py": (token.get("py") or "").strip(),
        }
        for token in words or []
        if isinstance(token, dict) and (token.get("cn") or "").strip()
    ]


def _slice_matching_tokens(target_cn: str, words: list) -> list:
    normalized_target = (target_cn or "").strip()
    normalized_words = _normalize_words(words)
    if not normalized_target or not normalized_words:
        return []

    for start in range(len(normalized_words)):
        buffer = ""
        matched = []
        for token in normalized_words[start:]:
            buffer += token["cn"]
            matched.append(token)
            if buffer == normalized_target:
                return matched
            if not normalized_target.startswith(buffer):
                break
    return []


def _render_line_pinyin(words: list) -> str:
    pieces = []
    for word in words or []:
        if not isinstance(word, dict):
            continue

        py = (word.get("py") or "").strip()
        cn = (word.get("cn") or "").strip()

        if py:
            if pieces and not pieces[-1].endswith((" ", "(", "\"", "'")):
                pieces.append(" ")
            pieces.append(py)
            continue

        punct = PUNCTUATION_MAP.get(cn, cn)
        if punct:
            pieces.append(punct)

    rendered = "".join(pieces).strip()
    return _capitalize_first_alpha(rendered)


def _build_dialogue_pinyin_lookup(data: dict) -> dict:
    lookup = {}
    dialogues = ((data.get("course_content") or {}).get("dialogues") or [])

    for dialogue_block in dialogues:
        if not isinstance(dialogue_block, dict):
            continue

        if "lines" in dialogue_block:
            for line in dialogue_block.get("lines", []):
                if not isinstance(line, dict):
                    continue
                words = line.get("words", [])
                cn = "".join(
                    token.get("cn", "")
                    for token in words
                    if isinstance(token, dict)
                ).strip()
                py = _render_line_pinyin(words)
                if cn and py:
                    lookup.setdefault(cn, py)
            continue

        cn = (dialogue_block.get("chinese") or "").strip()
        py = (dialogue_block.get("pinyin") or "").strip()
        if cn and py:
            lookup.setdefault(cn, py)

    return lookup


def _build_dialogue_tokens_lookup(data: dict) -> dict:
    lookup = {}
    dialogues = ((data.get("course_content") or {}).get("dialogues") or [])

    for dialogue_block in dialogues:
        if not isinstance(dialogue_block, dict):
            continue

        if "lines" in dialogue_block:
            for line in dialogue_block.get("lines", []):
                if not isinstance(line, dict):
                    continue
                words = line.get("words", [])
                cn = "".join(
                    token.get("cn", "")
                    for token in words
                    if isinstance(token, dict)
                ).strip()
                tokens = _normalize_words(words)
                if cn and tokens:
                    lookup.setdefault(cn, tokens)
            continue

        cn = (dialogue_block.get("chinese") or "").strip()
        words = dialogue_block.get("words", []) or dialogue_block.get("tokens", [])
        tokens = _normalize_words(words)
        if cn and tokens:
            lookup.setdefault(cn, tokens)

    return lookup


def _find_matching_tokens(sentence_cn: str, data: dict) -> list:
    target_cn = (sentence_cn or "").strip()
    if not target_cn:
        return []

    dialogues = ((data.get("course_content") or {}).get("dialogues") or [])
    for dialogue_block in dialogues:
        if not isinstance(dialogue_block, dict):
            continue

        if "lines" in dialogue_block:
            for line in dialogue_block.get("lines", []):
                if not isinstance(line, dict):
                    continue
                matched = _slice_matching_tokens(target_cn, line.get("words", []))
                if matched:
                    return matched
            continue

        words = dialogue_block.get("words", []) or dialogue_block.get("tokens", [])
        matched = _slice_matching_tokens(target_cn, words)
        if matched:
            return matched

    return []


def backfill_file(path: Path, apply: bool = False) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    pinyin_lookup = _build_dialogue_pinyin_lookup(data)
    tokens_lookup = _build_dialogue_tokens_lookup(data)
    vocabulary = ((data.get("course_content") or {}).get("vocabulary") or [])

    updated = 0
    unresolved = 0

    for item in vocabulary:
        if not isinstance(item, dict):
            continue

        example = item.get("example_sentence")
        if not isinstance(example, dict):
            continue

        cn = (example.get("cn") or "").strip()
        py = (example.get("py") or "").strip()
        tokens = example.get("tokens") or []
        if not cn or (py and tokens):
            continue

        recovered_tokens = tokens_lookup.get(cn, []) or _find_matching_tokens(cn, data)
        recovered = pinyin_lookup.get(cn, "")
        if not recovered and recovered_tokens:
            recovered = _render_line_pinyin(recovered_tokens)
        if recovered or recovered_tokens:
            if recovered:
                example["py"] = recovered
            if recovered_tokens:
                example["tokens"] = recovered_tokens
            updated += 1
        else:
            unresolved += 1

    if apply and updated:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    return {
        "file": str(path),
        "updated": updated,
        "unresolved": unresolved,
    }


def _build_lesson_lookup_map(lesson_dir: Path) -> dict:
    lesson_lookup = {}
    for path in iter_target_files(lesson_dir):
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        lesson_id = ((data.get("lesson_metadata") or {}).get("lesson_id"))
        if lesson_id is None:
            continue
        lesson_lookup[int(lesson_id)] = _build_dialogue_pinyin_lookup(data)
    return lesson_lookup


def backfill_global_vocab_memory(path: Path, lesson_dir: Path, apply: bool = False) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    lesson_lookup = _build_lesson_lookup_map(lesson_dir)
    lesson_token_lookup = {}
    for path in iter_target_files(lesson_dir):
        with open(path, "r", encoding="utf-8") as file:
            lesson_data = json.load(file)
        lesson_id = ((lesson_data.get("lesson_metadata") or {}).get("lesson_id"))
        if lesson_id is None:
            continue
        lesson_token_lookup[int(lesson_id)] = _build_dialogue_tokens_lookup(lesson_data)
    updated = 0
    unresolved = 0

    for entries in data.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue

            example = entry.get("example")
            if not isinstance(example, dict):
                continue

            cn = (example.get("cn") or "").strip()
            py = (example.get("py") or "").strip()
            tokens = example.get("tokens") or []
            if not cn or (py and tokens):
                continue

            lesson_id = entry.get("lesson_id")
            lesson_map = lesson_lookup.get(int(lesson_id)) if lesson_id is not None else None
            token_map = lesson_token_lookup.get(int(lesson_id)) if lesson_id is not None else None
            lesson_json_path = lesson_dir / f"lesson{int(lesson_id)}_data.json" if lesson_id is not None else None
            lesson_data = None
            if lesson_json_path and lesson_json_path.exists():
                with open(lesson_json_path, "r", encoding="utf-8") as lesson_file:
                    lesson_data = json.load(lesson_file)

            recovered_tokens = (token_map or {}).get(cn, []) or _find_matching_tokens(cn, lesson_data or {})
            recovered = (lesson_map or {}).get(cn, "")
            if not recovered and recovered_tokens:
                recovered = _render_line_pinyin(recovered_tokens)
            if recovered or recovered_tokens:
                if recovered:
                    example["py"] = recovered
                if recovered_tokens:
                    example["tokens"] = recovered_tokens
                updated += 1
            else:
                unresolved += 1

    if apply and updated:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    return {
        "file": str(path),
        "updated": updated,
        "unresolved": unresolved,
    }


def iter_target_files(target: Path):
    if target.is_file():
        yield target
        return

    for path in sorted(target.glob("*.json")):
        if path.is_file():
            yield path


def main():
    parser = argparse.ArgumentParser(description="Backfill missing vocabulary example pinyin from lesson dialogues.")
    parser.add_argument(
        "target",
        nargs="?",
        default=str(Path(__file__).resolve().parent.parent / "artifacts" / "integrated_chinese" / "synced_json"),
        help="JSON file or directory to process. Defaults to backend/content_builder/artifacts/integrated_chinese/synced_json.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write recovered pinyin back to the source files.",
    )
    parser.add_argument(
        "--global-memory",
        action="store_true",
        help="Backfill integrated_chinese vocab memory using synced_json lessons.",
    )
    args = parser.parse_args()

    if args.global_memory:
        global_path = Path(args.target).resolve()
        if global_path.is_dir():
            global_path = global_path / "global_vocab_memory.json"
        lesson_dir = Path(__file__).resolve().parent.parent / "artifacts" / "integrated_chinese" / "synced_json"
        if not global_path.exists():
            raise SystemExit(f"Target not found: {global_path}")
        if not lesson_dir.exists():
            raise SystemExit(f"Lesson directory not found: {lesson_dir}")
        summaries = [backfill_global_vocab_memory(global_path, lesson_dir, apply=args.apply)]
    else:
        target = Path(args.target).resolve()
        if not target.exists():
            raise SystemExit(f"Target not found: {target}")
        summaries = [backfill_file(path, apply=args.apply) for path in iter_target_files(target)]

    total_updated = sum(item["updated"] for item in summaries)
    total_unresolved = sum(item["unresolved"] for item in summaries)

    for item in summaries:
        if item["updated"] or item["unresolved"]:
            print(
                f"{Path(item['file']).name}: updated={item['updated']}, unresolved={item['unresolved']}"
            )

    mode = "Applied" if args.apply else "Dry run"
    print(
        f"{mode} complete. files={len(summaries)}, updated={total_updated}, unresolved={total_unresolved}"
    )


if __name__ == "__main__":
    main()
