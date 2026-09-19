#!/usr/bin/env python3
"""Versioned deterministic dish labeling. Bump VERSION when rules change."""
import json, re
from datetime import datetime, timezone
from pathlib import Path
VERSION="1.1.0"

def load(p,default):
    q=Path(p); return json.loads(q.read_text("utf-8")) if q.exists() else default
def aliases(groups):
    out={}
    for g in groups:
        names=g if isinstance(g,list) else g.get("names",[]); canonical=(g.get("canonical") if isinstance(g,dict) else names[0] if names else "")
        for n in names: out[n]=canonical
    return out
def infer_dish(title, known_names, ingredient_names):
    """Conservative title-only fallback; returns (name, referenced ingredients)."""
    text=re.sub(r"<[^>]+>","",title)
    bracket=re.search(r"【([^】]+)】",text)
    text=bracket.group(1) if bracket else text
    text=re.sub(r"[!！‼️?？~～|丨｜,，。:：;；]+"," ",text).strip()
    for name in sorted(known_names,key=len,reverse=True):
        if name in text: return name, None
    text=re.split(r"(?:超详细|保姆级|教程|配方|做法|怎么做|这样做|学会|出摊|安排上|太香了|绝了)",text,1)[0].strip()
    if "的" in text and re.search(r"(?:好吃|简单|有手|流泪|馋|必吃)",text): text=text.rsplit("的",1)[-1]
    text=re.sub(r"^(?:好吃到\S+|简单到\S+|今天做|教你做|来做一道)","",text).strip()
    text=re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]","",text)
    if not (2 <= len(text) <= 16): return None, None
    refs=sorted({x for x in ingredient_names if len(x)>=2 and x in text})
    food_hint=bool(refs or re.search(r"(?:鸡|鸭|鹅|鱼|虾|蟹|肉|排骨|面|饭|饼|汤|羹|粥|菜|蛋|豆腐|炒|炖|蒸|煮|烤|煎|炸|拌|烧|卤|焖)$",text))
    return (text,refs) if food_hint else (None,None)
def main():
    raw=load("村驴/raw.json",{"videos":[]}); dishes=load("base/dishes.json",{}); ingredient_table=load("base/ingredients.json",{}); amap=aliases(load("base/dish_alias_groups.json",[]))
    candidates=sorted(set(dishes)|set(amap),key=len,reverse=True); output=[]
    for v in raw.get("videos",[]):
        hay=(v.get("title","")+"\n"+v.get("description","")).lower()
        matched=[]
        for name in candidates:
            if name.lower() in hay:
                canonical=amap.get(name,name)
                if canonical in dishes and canonical not in matched: matched.append(canonical)
        if not matched:
            inferred, refs=infer_dish(v.get("title",""),set(dishes)|set(amap),set(ingredient_table))
            if inferred:
                if inferred not in dishes:
                    dishes[inferred]={"name":inferred,"ingredients":refs or [],"special_tools":[],"sources":[f"bilibili:{v.get('bvid','')}"],"auto_generated":True,"needs_review":True}
                matched=[inferred]
        item=dict(v); item["数据标记程序版本号"]=VERSION; item["菜名"]=matched; output.append(item)
    out={"schema_version":1,"labeler_version":VERSION,"generated_at":datetime.now(timezone.utc).isoformat(),"videos":output}
    Path("村驴/videos.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n","utf-8")
    Path("base/dishes.json").write_text(json.dumps(dict(sorted(dishes.items())),ensure_ascii=False,indent=2)+"\n","utf-8")
    print(f"labeled={len(output)} version={VERSION}")
if __name__=="__main__": main()
