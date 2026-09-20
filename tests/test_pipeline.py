import json, subprocess, sys, unittest
from pathlib import Path
from scripts.build_base import normalize_ingredients
class PipelineTest(unittest.TestCase):
    def test_seed_json_and_validation(self):
        for p in ["村驴/raw.json","村驴/videos.json","base/dishes.json","base/ingredients.json","base/dish_alias_groups.json","base/ingredient_alias_groups.json"]:
            json.loads(Path(p).read_text("utf-8"))
        subprocess.run([sys.executable,"scripts/label.py"],check=True)
        subprocess.run([sys.executable,"scripts/validate.py"],check=True)
    def test_ingredient_normalization(self):
        self.assertEqual(normalize_ingredients("125ml 淡奶油"), ["淡奶油"])
        self.assertEqual(normalize_ingredients("五花肉/瘦肉"), ["五花肉", "瘦肉"])
        self.assertEqual(normalize_ingredients("大蒜5-6 瓣"), ["大蒜"])
        self.assertEqual(normalize_ingredients("搅拌机/料理机"), [])
if __name__ == "__main__": unittest.main()
