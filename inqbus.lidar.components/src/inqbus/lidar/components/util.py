import ntpath


def get_file_from_path(file_path):
    return ntpath.basename(file_path)
