import shutil
import os


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    source = f'{dir_path}/../www'
    destination = f'{dir_path}/../../../remote_logging_backend/experiments/frontend'
    if os.path.exists(destination):
        shutil.rmtree(destination)
    shutil.copytree(source, destination, dirs_exist_ok=True)
