"""Load a SerBot pilot episode without ROS2 or ML dependencies."""

import csv
import json
import sys
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _warn(message):
    print(f"WARNING: {message}", file=sys.stderr)


def _to_number_if_possible(value):
    if value is None:
        return value

    text = str(value).strip()
    if text == "":
        return text

    try:
        return float(text)
    except ValueError:
        return text


def _read_actions_csv(actions_path):
    if not actions_path.exists():
        raise FileNotFoundError(f"actions.csv 파일이 없습니다: {actions_path}")

    with actions_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            raise ValueError(f"actions.csv 헤더를 읽을 수 없습니다: {actions_path}")

        actions = []
        for row in reader:
            clean_row = {key: _to_number_if_possible(value) for key, value in row.items()}
            actions.append(clean_row)

    if not actions:
        raise ValueError(f"actions.csv에 데이터 행이 없습니다: {actions_path}")
    return actions


def _read_meta_json(meta_path):
    if not meta_path.exists():
        raise FileNotFoundError(f"meta.json 파일이 없습니다: {meta_path}")

    with meta_path.open("r", encoding="utf-8-sig") as json_file:
        return json.load(json_file)


def _list_frames(frames_dir):
    if not frames_dir.exists():
        _warn(f"frames 폴더가 없습니다. actions.csv 기준으로 dry-run을 계속합니다: {frames_dir}")
        return []

    frames = [
        str(path)
        for path in sorted(frames_dir.iterdir())
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]

    if not frames:
        _warn(f"frames 폴더에 이미지가 없습니다. actions.csv 기준으로 dry-run을 계속합니다: {frames_dir}")
    return frames


def load_episode(episode_dir):
    """Read frames list, goal.jpg path, actions.csv, and meta.json.

    goal.jpg and frame images are allowed to be missing during early dry-run.
    actions.csv and meta.json are required because they define the episode.
    """
    episode_path = Path(episode_dir).expanduser().resolve()
    if not episode_path.exists():
        raise FileNotFoundError(f"episode 폴더가 없습니다: {episode_path}")
    if not episode_path.is_dir():
        raise NotADirectoryError(f"episode 경로가 폴더가 아닙니다: {episode_path}")

    frames_dir = episode_path / "frames"
    goal_image_path = episode_path / "goal.jpg"
    actions_path = episode_path / "actions.csv"
    meta_path = episode_path / "meta.json"

    frames = _list_frames(frames_dir)

    if not goal_image_path.exists():
        _warn(f"goal.jpg 파일이 없습니다. goal image 없이 dry-run을 계속합니다: {goal_image_path}")

    actions = _read_actions_csv(actions_path)
    meta = _read_meta_json(meta_path)

    return {
        "episode_dir": str(episode_path),
        "frames": frames,
        "goal_image": str(goal_image_path),
        "actions": actions,
        "meta": meta,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python load_serbot_episode.py <episode_dir>")
        raise SystemExit(2)

    episode = load_episode(sys.argv[1])
    print(json.dumps(episode, ensure_ascii=False, indent=2))
