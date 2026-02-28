import os


async def get_folders_only(path):
    """Возвращает только папки в указанной директории"""
    folders = []
    for item in os.listdir(path):
        full_path = os.path.join(path, item)
        if os.path.isdir(full_path):
            folders.append(item)
    return folders

