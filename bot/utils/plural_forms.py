def get_plural_forms(x):
    lastTwoDigits = x % 100
    tens = lastTwoDigits // 10
    if tens == 1:
        return 2
    ones = lastTwoDigits % 10
    if ones == 1:
        return 0
    return 1 if ones >= 2 and ones <= 4 else 2
