import os
from pathlib import Path

import deepdoctection as dd

analyzer = dd.get_dd_analyzer()


def get_filename(path):
    return os.path.splitext(os.path.split(path)[1])[0]


def analyse_file(path):
    filename = get_filename(path)
    df = analyzer.analyze(path=path)
    df.reset_state()

    file_dir = path.parent.parent / f"json/{filename}"
    file_dir.mkdir(parents=True, exist_ok=True)
    for page in iter(df):
        page_path = file_dir / f"page{page.page_number + 1}.json"
        # page.save(path=page_path, image_to_json=False, highest_hierarchy_only=True)
        page.save(path=page_path, image_to_json=False)


if __name__ == '__main__':
    storage_path = Path(os.path.expanduser('~/Enter/docalchemy/storage'))
    file_path = storage_path / "pdf/600016.pdf"
    analyse_file(file_path.absolute())
