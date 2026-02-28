from datetime import datetime
import os


async def error_safe(def_name, error_text):
    folder_path = f"errors/{def_name}"
    os.makedirs(folder_path, exist_ok=True)
    with open(f"{folder_path}/error.txt", "a") as f:
        f.write(datetime.now().strftime("%H:%M %d:%m:%Y")+"\n"+str(error_text)+"\n\n")
    return 