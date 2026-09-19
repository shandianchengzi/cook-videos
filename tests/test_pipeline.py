import json, subprocess, sys, unittest
from pathlib import Path
class PipelineTest(unittest.TestCase):
    def test_seed_json_and_validation(self):
        for p in ["村驴/raw.json","村驴/videos.json","base/dishes.json","base/ingredients.json","base/dish_alias_groups.json","base/ingredient_alias_groups.json"]:
            json.loads(Path(p).read_text("utf-8"))
        subprocess.run([sys.executable,"scripts/label.py"],check=True)
        subprocess.run([sys.executable,"scripts/validate.py"],check=True)
if __name__ == "__main__": unittest.main()
