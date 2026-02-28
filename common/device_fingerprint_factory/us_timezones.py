"""
美国时区常量 + DST 支持

仅限美国地区时区，用于指纹-IP 地理一致性。
自动根据当前日期判断是否在夏令时期间。
"""

from datetime import datetime, timezone

from .signals import _deterministic_seed, _seed_to_int

# 美国时区定义
# offset_std: 标准时间偏移, offset_dst: 夏令时偏移
US_TIMEZONES = [
    {
        "name": "America/New_York",
        "offset_std": -5,
        "offset_dst": -4,
        "abbr_std": "EST",
        "abbr_dst": "EDT",
        "label": "Eastern Time",
    },
    {
        "name": "America/Chicago",
        "offset_std": -6,
        "offset_dst": -5,
        "abbr_std": "CST",
        "abbr_dst": "CDT",
        "label": "Central Time",
    },
    {
        "name": "America/Denver",
        "offset_std": -7,
        "offset_dst": -6,
        "abbr_std": "MST",
        "abbr_dst": "MDT",
        "label": "Mountain Time",
    },
    {
        "name": "America/Los_Angeles",
        "offset_std": -8,
        "offset_dst": -7,
        "abbr_std": "PST",
        "abbr_dst": "PDT",
        "label": "Pacific Time",
    },
    {
        "name": "America/Anchorage",
        "offset_std": -9,
        "offset_dst": -8,
        "abbr_std": "AKST",
        "abbr_dst": "AKDT",
        "label": "Alaska Time",
    },
    {
        "name": "Pacific/Honolulu",
        "offset_std": -10,
        "offset_dst": -10,  # 夏威夷不实行夏令时
        "abbr_std": "HST",
        "abbr_dst": "HST",
        "label": "Hawaii Time",
    },
]


def _is_us_dst(dt: datetime = None) -> bool:
    """
    判断当前日期是否在美国夏令时期间。

    美国 DST 规则 (2007 年至今):
    - 开始: 3 月第 2 个星期日 2:00 AM
    - 结束: 11 月第 1 个星期日 2:00 AM
    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    year = dt.year
    month = dt.month

    # 快速排除
    if month < 3 or month > 11:
        return False
    if 4 <= month <= 10:
        return True

    # 3 月: 第 2 个星期日之后
    if month == 3:
        # 查找第 2 个星期日
        first_day_weekday = datetime(year, 3, 1).weekday()  # 0=Mon, 6=Sun
        # 第一个星期日
        first_sunday = 1 + (6 - first_day_weekday) % 7
        second_sunday = first_sunday + 7
        return dt.day >= second_sunday

    # 11 月: 第 1 个星期日之前
    if month == 11:
        first_day_weekday = datetime(year, 11, 1).weekday()
        first_sunday = 1 + (6 - first_day_weekday) % 7
        return dt.day < first_sunday

    return False


def _get_tz_offset(tz_entry: dict) -> int:
    """根据当前是否 DST 返回对应偏移"""
    if _is_us_dst():
        return tz_entry["offset_dst"]
    return tz_entry["offset_std"]


def _get_tz_abbr(tz_entry: dict) -> str:
    """根据当前是否 DST 返回对应缩写"""
    if _is_us_dst():
        return tz_entry["abbr_dst"]
    return tz_entry["abbr_std"]


# 大陆时区 (排除 Alaska/Hawaii，占 96%+ 人口)
US_MAINLAND_TIMEZONES = [
    tz for tz in US_TIMEZONES if tz["offset_std"] >= -8
]


def select_timezone(verification_id: str) -> dict:
    """
    确定性选择美国大陆时区，自动处理 DST。

    Returns:
        dict with keys: name, offset, abbr, label
    """
    seed = _deterministic_seed(verification_id, "timezone_select")
    idx = _seed_to_int(seed, len(US_MAINLAND_TIMEZONES))
    tz = US_MAINLAND_TIMEZONES[idx]
    return {
        "name": tz["name"],
        "offset": _get_tz_offset(tz),
        "abbr": _get_tz_abbr(tz),
        "label": tz["label"],
    }
