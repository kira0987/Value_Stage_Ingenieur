import os

def delete_empty_folders(root_folder):
    deleted = False
    for dirpath, dirnames, filenames in os.walk(root_folder, topdown=False):
        if not filenames and not dirnames:
            try:
                os.rmdir(dirpath)
                print(f"Deleted empty folder: {dirpath}")
                deleted = True
            except OSError as e:
                print(f"Failed to delete {dirpath}: {e}")
    return deleted

save_folder = "catalog data"
if not os.path.exists(save_folder):
    print(f"Folder {save_folder} does not exist.")
    exit()

while delete_empty_folders(save_folder):
    pass

print("All empty folders have been deleted.")