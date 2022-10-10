import os
import requests
import zipfile


class ModelLoadError(Exception):
    pass


def download_models(model_dir: str, download_urls: [str]) -> None:
    try:
        os.mkdir(os.path.join(model_dir, '.lock'))
    except FileExistsError as err:
        return  # already downloaded or initiated

    try:
        for url in download_urls:
            # download model
            model = requests.get(url)

            # store model
            path = os.path.join(model_dir, os.path.basename(url))
            with open(path, 'wb') as zipFile:
                zipFile.write(model.content)

                # unzip model
                with zipfile.ZipFile(path, 'r') as zip_ref:
                    zip_ref.extractall(model_dir)

            # remove download (.zip)
            os.remove(path)

    except Exception as err:
        raise ModelLoadError(err)
