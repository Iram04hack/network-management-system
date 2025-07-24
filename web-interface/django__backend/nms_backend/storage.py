from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.files.storage import FileSystemStorage
import os

class CustomStaticFilesStorage(StaticFilesStorage):
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            # Si le fichier existe déjà, on ajoute un suffixe numérique
            dir_name, file_name = os.path.split(name)
            file_root, file_ext = os.path.splitext(file_name)
            counter = 1

            while self.exists(name):
                name = os.path.join(dir_name, f"{file_root}_{counter}{file_ext}")
                counter += 1

        return name 