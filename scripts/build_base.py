#!/usr/bin/env python3
"""Convert the raw reference corpus into human-editable relational JSON tables."""
import json, re
from pathlib import Path

def clean(s): return re.sub(r"[`*_\[\]（）()]", "", s).strip(" ：:，,。\t")
def main():
    text=Path("reference/howtocook-recipes.txt").read_text("utf-8")
    blocks=re.split(r"^===== FILE: (.+?) =====$",text,flags=re.M)[1:]; dishes={}; ingredients={}
    for path,body in zip(blocks[0::2],blocks[1::2]):
        title=next((clean(x[2:]) for x in body.splitlines() if x.startswith("# ")),Path(path).stem)
        section=""; dish_ings=[]; tools=[]
        for line in body.splitlines():
            if line.startswith("## "): section=clean(line[3:]); continue
            if not re.match(r"^\s*[-*]\s+",line): continue
            item=clean(re.sub(r"^\s*[-*]\s+", "", line).split("：",1)[0].split(":",1)[0])
            item=re.sub(r"\s+[0-9一二三四五六七八九十半适少若].*$", "", item).strip()
            if not item or len(item)>30: continue
            if any(k in section for k in ("原料","食材","必备原料")):
                ingredients.setdefault(item,{"name":item,"processing_methods":[],"notes":[],"sources":[]})
                if path not in ingredients[item]["sources"]: ingredients[item]["sources"].append(path)
                dish_ings.append(item)
            elif any(k in section for k in ("工具","厨具")): tools.append(item)
        if dish_ings: dishes[title]={"name":title,"ingredients":sorted(set(dish_ings)),"special_tools":sorted(set(tools)),"sources":[path]}
    Path("base/dishes.json").write_text(json.dumps(dict(sorted(dishes.items())),ensure_ascii=False,indent=2)+"\n","utf-8")
    Path("base/ingredients.json").write_text(json.dumps(dict(sorted(ingredients.items())),ensure_ascii=False,indent=2)+"\n","utf-8")
    print(f"dishes={len(dishes)} ingredients={len(ingredients)}")
if __name__=="__main__": main()

