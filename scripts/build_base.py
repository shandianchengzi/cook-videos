#!/usr/bin/env python3
"""Convert the raw reference corpus into human-editable relational JSON tables."""
import json, re
from pathlib import Path

def clean(s): return re.sub(r"[`*_\[\]（）()]", "", s).strip(" ：:，,。\t")
UNITS=r"(?:毫升|ml|mL|ML|升|克|kg|g|千克|斤|两|个|只|片|块|根|颗|粒|瓣|勺|汤匙|茶匙|杯|袋|盒|把|撮|滴|厘米|cm)"
TOOL_WORDS=("锅","碗","杯","勺","盆","机","炉","灶","模具","簸箕","刀","砧板")
def normalize_ingredients(value):
    """Return ingredient names only; split alternatives and discard measures/tools."""
    value=re.sub(r"!?\[[^\]]*\]\([^)]*\)|\.\.?/\S+|!\S+\.(?:png|jpe?g|webp)","",value,flags=re.I)
    value=re.sub(r"（[^）]*）|\([^)]*\)","",value)
    value=re.sub(r"^\s*[0-9０-９一二三四五六七八九十半]+(?:\s*[-~—至]\s*[0-9０-９一二三四五六七八九十半]+)?\s*"+UNITS+r"\s*","",value,flags=re.I)
    result=[]
    for part in re.split(r"[/／]",value):
        part=re.sub(r"\b(?:and|or)\b.*$","",part,flags=re.I)
        part=re.sub(r"\s*[0-9０-９一二三四五六七八九十半]+(?:\s*[-~—至]\s*[0-9０-９一二三四五六七八九十半]+)?\s*"+UNITS+r".*$","",part,flags=re.I)
        part=re.sub(r"\s+.*$","",part).strip()
        part=re.sub(r"(?:可选|备选|选其一即可|适量|少许|若干)$","",part)
        part=part.strip(" .。…、，,;；:：-—")
        if not part or len(part)>16 or re.search(r"\d",part): continue
        if any(part.endswith(x) for x in TOOL_WORDS) and part not in ("火锅底料",): continue
        result.append(part)
    return list(dict.fromkeys(result))
def main():
    text=Path("reference/howtocook-recipes.txt").read_text("utf-8")
    blocks=re.split(r"^===== FILE: (.+?) =====$",text,flags=re.M)[1:]; dishes={}; ingredients={}
    for path,body in zip(blocks[0::2],blocks[1::2]):
        title=next((clean(x[2:]) for x in body.splitlines() if x.startswith("# ")),Path(path).stem)
        title=re.sub(r"的做法$", "", title).strip()
        section=""; dish_ings=[]; tools=[]
        for line in body.splitlines():
            if line.startswith("## "): section=clean(line[3:]); continue
            if not re.match(r"^\s*[-*]\s+",line): continue
            item=clean(re.sub(r"^\s*[-*]\s+", "", line).split("：",1)[0].split(":",1)[0])
            if not item or len(item)>60: continue
            if any(k in section for k in ("原料","食材","必备原料")):
                for name in normalize_ingredients(item):
                    ingredients.setdefault(name,{"name":name,"processing_methods":[],"notes":[],"sources":[]})
                    if path not in ingredients[name]["sources"]: ingredients[name]["sources"].append(path)
                    dish_ings.append(name)
            elif any(k in section for k in ("工具","厨具")): tools.append(item)
        if dish_ings: dishes[title]={"name":title,"ingredients":sorted(set(dish_ings)),"special_tools":sorted(set(tools)),"sources":[path]}
    Path("base/dishes.json").write_text(json.dumps(dict(sorted(dishes.items())),ensure_ascii=False,indent=2)+"\n","utf-8")
    Path("base/ingredients.json").write_text(json.dumps(dict(sorted(ingredients.items())),ensure_ascii=False,indent=2)+"\n","utf-8")
    print(f"dishes={len(dishes)} ingredients={len(ingredients)}")
if __name__=="__main__": main()
