def format_duration(milliseconds: int) -> str:
    if milliseconds < 0:
        milliseconds = 0
    total_seconds, millis = divmod(milliseconds, 1000)
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}.{millis // 100}"


def format_clock(milliseconds: int) -> str:
    if milliseconds < 0:
        milliseconds = 0
    total_seconds = milliseconds // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"
