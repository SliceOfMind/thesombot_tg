def strike_text(line):
    result = ''
    for char in str(line):
        result += char + '\u0336'

    return result
