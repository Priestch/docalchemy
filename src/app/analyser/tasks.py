import importlib.util
import sys
from pathlib import Path

from .storage_service import storage
from celery import Celery

app = Celery("app", broker="redis://redis:6379/0")

print(sys.path)


def import_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@app.task
def analyse_document(filename: str, lib: str, **kwargs):
    file_path = storage.resolve(filename)
    analyser_module = import_from_path(f"{lib}_analyser", Path(__file__).parent / (lib + ".py"))
    analyser = analyser_module.Analyser.configure(**kwargs)
    analyser.analyse(file_path)
