def save_settings(volume: int = None, fullscreen: bool = None, ):
    settings = read_settings()
    if volume is not None:
        settings["volume"] = volume
    if fullscreen is not None:
        settings["fullscreen"] = int(fullscreen)
    with open("assets/settings.txt", "w") as file:
        lines = [f"{i};{int(settings[i])}\n" for i in settings.keys()]
        file.writelines(lines)

def read_settings():
    res = {}
    try:
        with open("assets/settings.txt", "r") as file:
            lines = [i.rstrip("\n").split(";") for i in file.readlines()]
            for line in lines:
                if line[0] == "volume":
                    res["volume"] = int(line[1])
                elif line[0] == "fullscreen":
                    res["fullscreen"] = bool(int(line[1]))
    except FileNotFoundError:
        pass
    return res