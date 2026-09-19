#!/usr/bin/env python3
import json
from pathlib import Path
def main():
    dishes=json.loads(Path("base/dishes.json").read_text("utf-8")); ingredients=json.loads(Path("base/ingredients.json").read_text("utf-8"))
    missing={d:sorted(set(v.get("ingredients",[]))-set(ingredients)) for d,v in dishes.items()}; missing={k:v for k,v in missing.items() if v}
    if missing: raise SystemExit("dish -> unknown ingredients: "+json.dumps(missing,ensure_ascii=False))
    raw=json.loads(Path("村驴/raw.json").read_text("utf-8")); bv=[v.get("bvid") for v in raw["videos"]]
    if None in bv or len(bv)!=len(set(bv)): raise SystemExit("raw.json contains missing/duplicate bvid")
    tagged=json.loads(Path("村驴/videos.json").read_text("utf-8"))
    unknown={x for v in tagged["videos"] for x in v.get("dish_names",[])}-set(dishes)
    if unknown: raise SystemExit("labels reference unknown dishes: "+str(unknown))
    print("validation ok")
if __name__=="__main__": main()
