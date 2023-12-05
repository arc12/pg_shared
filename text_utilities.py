from time import time

def lang_periods(lang):
    # TODO make this respect lang for non-English cases
    return {"m": "minutes", "h": "hours", "d": "days", "a": "ago"}

def ago_text(event_timestamp, lang):
    lp = lang_periods(lang)
    ago = round((int(time()) - event_timestamp) / 60, 0)  # minutes ago
    if ago >=60:
        ago = round(ago / 60, 0)  # hours ago
        if ago >= 24:
            ago = round(ago / 24)
            ago_units = lp["d"]
        else:
            ago_units = lp["h"]
    else:
        ago_units = lp["m"]
    if ago == 1:
        ago_units = ago_units[:-1]                
    return f"{ago:.0f} {ago_units} {lp['a']}"