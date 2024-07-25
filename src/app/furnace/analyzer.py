from pathlib import Path

import deepdoctection as dd
from server.storage import storage

d_analyzer = dd.get_dd_analyzer()


class Analyzer:
    def __init__(self, file_storage: "Storage"):
        self.storage = file_storage

    def analyze(self, file: Path):
        df = d_analyzer.analyze(path=file)
        df.reset_state()

        output_dir = self.storage.ensure_analyse_dir(file)
        for page in iter(df):
            page_path = output_dir / f"page{page.page_number + 1}.json"
            page.save(path=page_path, image_to_json=False, highest_hierarchy_only=True)
            # page.save(path=page_path, image_to_json=False)


if __name__ == "__main__":
    analyzer = Analyzer(file_storage=storage)
    file_path = fild_path = Path("/home/gaopeng/Enter/docalchemy-space/storage/files/demo/demo.pdf")
    analyzer.analyze(file_path)
