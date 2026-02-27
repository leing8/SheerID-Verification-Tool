"""
美国时区常量

仅限美国地区时区，用于指纹-IP 地理一致性。
"""

US_TIMEZONES = [
    {
        "name": "America/New_York",
        "offset": -5,
        "abbr": "EST",
        "label": "Eastern Time",
    },
    {
        "name": "America/Chicago",
        "offset": -6,
        "abbr": "CST",
        "label": "Central Time",
    },
    {
        "name": "America/Denver",
        "offset": -7,
        "abbr": "MST",
        "label": "Mountain Time",
    },
    {
        "name": "America/Los_Angeles",
        "offset": -8,
        "abbr": "PST",
        "label": "Pacific Time",
    },
    {
        "name": "America/Anchorage",
        "offset": -9,
        "abbr": "AKST",
        "label": "Alaska Time",
    },
    {
        "name": "Pacific/Honolulu",
        "offset": -10,
        "abbr": "HST",
        "label": "Hawaii Time",
    },
]

# 大陆时区 (排除 Alaska/Hawaii，占 96%+ 人口)
US_MAINLAND_TIMEZONES = [tz for tz in US_TIMEZONES if tz["offset"] >= -8]
