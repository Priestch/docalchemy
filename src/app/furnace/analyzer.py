import json
from pathlib import Path
from zipfile import ZipFile

import deepdoctection as dd


class Analyzer:
    d_analyzer = None

    def __init__(self):
        if Analyzer.d_analyzer is None:
            Analyzer.d_analyzer = dd.get_dd_analyzer()

    def analyze(self, file: Path) -> Path:
        df = self.d_analyzer.analyze(path=file, output="dict")
        df.reset_state()

        zipfile_path = file.with_suffix('.zip')
        with ZipFile(zipfile_path, 'w') as myzip:
            for page in iter(df):
                page_num = page.get("page_number")
                myzip.writestr(f"page{page_num}.json", json.dumps(page))

        return zipfile_path


if __name__ == "__main__":
    analyzer = Analyzer()
    file_path = fild_path = Path("/home/gaopeng/Enter/docalchemy/storage/2ac25d73f4db8c78b6b1613337bc5182.pdf")
    analyzer.analyze(file_path)
