from PIL import ImageColor, ImageFont

def caption_time(t):
    cs = max(0, round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"

def caption_colour(colour):
    r, g, b = ImageColor.getrgb(colour)[:3]
    return f"&H00{b:02X}{g:02X}{r:02X}"

def caption_escape(text):
    return text.replace("\\", "/").replace("{", "(").replace("}", ")")

def build_caption(words, width, height, config):
    font, padding = config["font"], config["padding"]
    family, style = ImageFont.truetype(font["path"], 10).getname()
    bold = -1 if "bold" in (style or "").lower() else 0
    side_margin = int(width * 0.1)  # caption box = 80% of video width, like before

    groups, current = [], []
    for word in words:
        current.append(word)
        if len(current) == config["words_per_caption"] or word[0][-1] in ".?!":
            groups.append(current)
            current = []
    if current:
        groups.append(current)

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {width}",
        f"PlayResY: {height}",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{family},{font['size']},{caption_colour(font['color'])},{caption_colour(font['color'])},"
        f"{caption_colour(font['stroke_color'])},&H00000000,{bold},0,0,0,100,100,0,0,1,{font['stroke_width']},0,"
        f"5,{side_margin},{side_margin},0,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for i, group in enumerate(groups):
        text = caption_escape(" ".join(word for word, _, _ in group))
        start = padding + group[0][1]
        end = padding + (groups[i + 1][0][1] if i + 1 < len(groups) else group[-1][2])
        lines.append(f"Dialogue: 0,{caption_time(start)},{caption_time(end)},Default,,0,0,0,,{text}")
    return "\n".join(lines) + "\n"