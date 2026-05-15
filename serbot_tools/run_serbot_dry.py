"""Print-only SerBot dry-run for the OmniVLA adapter pipeline.

This script does not run OmniVLA, does not import torch/transformers, and does
not publish ROS2 messages. It only checks the episode loader and waypoint to
cmd_vel conversion.
"""

import argparse
import sys
from pathlib import Path

try:
    from load_serbot_episode import load_episode
    from waypoint_to_cmdvel import waypoint_to_cmdvel
except ImportError:
    # Allows: python -m serbot_tools.run_serbot_dry
    from .load_serbot_episode import load_episode
    from .waypoint_to_cmdvel import waypoint_to_cmdvel


DUMMY_WAYPOINTS = [
    [0.05, 0.00, 1.0, 0.0],
    [0.05, 0.02, 1.0, 0.0],
    [0.00, 0.00, 1.0, 0.0],
]


def _frame_name_from_action(action, index):
    image_name = action.get("image")
    if image_name:
        return Path(str(image_name)).name
    return f"frame_{index + 1:06d}.jpg"


def run_dry(episode_dir):
    episode = load_episode(episode_dir)
    actions = episode["actions"]

    print(f"episode={episode['episode_dir']}")
    print(f"actions={len(actions)}")
    print("mode=print-only dry-run")

    for index, action in enumerate(actions):
        waypoint = DUMMY_WAYPOINTS[min(index, len(DUMMY_WAYPOINTS) - 1)]
        cmdvel = waypoint_to_cmdvel(waypoint)
        frame_name = _frame_name_from_action(action, index)

        print(
            f"frame={frame_name} "
            f"linear_x={cmdvel['linear_x']:.3f} "
            f"angular_z={cmdvel['angular_z']:.3f}"
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run SerBot print-only dry-run without OmniVLA/ROS2 dependencies."
    )
    parser.add_argument(
        "--episode",
        required=True,
        help="Path to episode folder, e.g. serbot_data/episode_001",
    )
    args = parser.parse_args(argv)

    try:
        run_dry(args.episode)
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
