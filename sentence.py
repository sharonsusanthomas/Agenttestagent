import re

def clean_to_one_sentence(text,
                          allowed_punct=".,?:-()",
                          normalize_dashes=True):
    # 1) normalize common dash characters to ascii hyphen
    if normalize_dashes:
        text = re.sub(r"[\u2012\u2013\u2014\u2015]", "-", text)

    # 2) collapse newlines and tabs to single space
    text = re.sub(r"[\r\n\t]+", " ", text)

    # 3) remove characters NOT in allowed set (letters, digits, spaces, allowed punctuation)
    safe_punct = re.escape(allowed_punct)
    pattern = rf"[^A-Za-z0-9\s{safe_punct}]"
    text = re.sub(pattern, "", text)

    # 4) collapse multiple spaces to single space, trim ends
    text = re.sub(r"\s+", " ", text).strip()

    # 5) keep up to the first sentence terminator (. ? !)
    m = re.search(r"[.?!]", text)
    if m:
        text = text[: m.end() ]
    return text


# -------- MAIN ----------
if __name__ == "__main__":
    print("Enter your paragraph (press Enter twice to finish):")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    user_input = "\n".join(lines)

    cleaned = clean_to_one_sentence(user_input)
    print("\nCleaned single-line output:\n", cleaned)
