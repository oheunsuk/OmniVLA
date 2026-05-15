"""Convert an OmniVLA waypoint into SerBot-friendly cmd_vel values.

This file has no ROS2, torch, or transformers dependency. It is meant for
local dry-run checks before any real robot command is published.
"""

import math


def _clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def _safe_float(value, default=0.0):
    """Convert value to a finite float. NaN/Inf becomes default."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(number):
        return default
    return number


def _clip_angle(angle):
    """Normalize angle to [-pi, pi]."""
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def _limit_velocity_pair(linear, angular, max_linear, max_angular):
    """Apply the same style of final velocity limit used in run_omnivla.py."""
    linear = _safe_float(linear)
    angular = _safe_float(angular)

    max_linear = abs(_safe_float(max_linear, 0.3))
    max_angular = abs(_safe_float(max_angular, 0.3))

    if max_linear == 0.0 or max_angular == 0.0:
        return 0.0, 0.0

    if abs(linear) <= max_linear:
        if abs(angular) <= max_angular:
            limited_linear = linear
            limited_angular = angular
        else:
            rd = linear / angular if abs(angular) > 1e-12 else 0.0
            limited_linear = max_angular * math.copysign(abs(rd), linear)
            limited_angular = math.copysign(max_angular, angular)
    else:
        if abs(angular) <= 0.001:
            limited_linear = math.copysign(max_linear, linear)
            limited_angular = 0.0
        else:
            rd = linear / angular
            if abs(rd) >= max_linear / max_angular:
                limited_linear = math.copysign(max_linear, linear)
                limited_angular = math.copysign(max_linear / abs(rd), angular)
            else:
                limited_linear = max_angular * math.copysign(abs(rd), linear)
                limited_angular = math.copysign(max_angular, angular)

    # SerBot initial dry-run uses forward-only linear velocity.
    limited_linear = _clamp(_safe_float(limited_linear), 0.0, max_linear)
    limited_angular = _clamp(_safe_float(limited_angular), -max_angular, max_angular)
    return limited_linear, limited_angular


def waypoint_to_cmdvel(waypoint, dt=1 / 3, max_linear=0.3, max_angular=0.3):
    """Convert [dx, dy, hx, hy] into {"linear_x": float, "angular_z": float}.

    dx, dy are waypoint position offsets in the robot local frame.
    hx, hy are heading hints used when the waypoint position is almost zero.
    """
    if waypoint is None or len(waypoint) < 4:
        raise ValueError("waypoint는 [dx, dy, hx, hy] 형식의 길이 4 리스트여야 합니다.")

    dt = _safe_float(dt, 1 / 3)
    if dt <= 0.0:
        raise ValueError("dt는 0보다 큰 값이어야 합니다.")

    dx, dy, hx, hy = [_safe_float(value) for value in waypoint[:4]]

    eps = 1e-8
    if abs(dx) < eps and abs(dy) < eps:
        # 위치 이동량이 거의 없으면 heading 방향만 보고 제자리 회전합니다.
        linear = 0.0
        angular = _clip_angle(math.atan2(hy, hx)) / dt
    elif abs(dx) < eps:
        # x 이동량 없이 y만 있으면 좌/우 90도 방향으로 회전합니다.
        linear = 0.0
        angular = math.copysign(math.pi / (2.0 * dt), dy)
    else:
        linear = dx / dt
        angular = math.atan(dy / dx) / dt

    # 원본 코드의 1차 제한: linear는 전진만 허용합니다.
    linear = _clamp(_safe_float(linear), 0.0, 0.5)
    angular = _clamp(_safe_float(angular), -1.0, 1.0)

    linear, angular = _limit_velocity_pair(linear, angular, max_linear, max_angular)

    return {
        "linear_x": float(linear),
        "angular_z": float(angular),
    }


if __name__ == "__main__":
    samples = [
        [0.05, 0.00, 1.0, 0.0],
        [0.05, 0.02, 1.0, 0.0],
        [0.00, 0.00, 1.0, 0.0],
    ]
    for sample in samples:
        print(sample, waypoint_to_cmdvel(sample))
