def recognize_letter(fingers):
    letter_map = {
        (1, 0, 0, 0, 0): "A",
        (0, 1, 1, 1, 1): "B",
        (0, 1, 0, 0, 0): "D",
        (0, 0, 0, 0, 0): "E",
        (0, 0, 1, 1, 1): "F",
        (0, 0, 0, 0, 1): "I",
        (1, 1, 0, 0, 0): "L",
        (0, 1, 1, 0, 0): "V",
        (0, 1, 1, 1, 0): "W",
        (1, 0, 0, 0, 1): "Y"
    }
    return letter_map.get(tuple(fingers), "")
