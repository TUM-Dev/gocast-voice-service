import os
import requests
import zipfile


class ModelLoadError(Exception):
    pass


def download_models(model_dir: str, download_urls: [str]) -> None:
    """Download language models if non-existing.

    Args:
        model_dir (str): The path to where the language models should be stored.
        download_urls ([str]): URLs pointing to VOSK Language Models.
    """
    try:
        os.mkdir(os.path.join(model_dir, '.lock'))
    except FileExistsError:
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
