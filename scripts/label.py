#!/usr/bin/env python3
"""Versioned deterministic dish labeling. Bump VERSION when rules change."""
import json, re
from datetime import datetime, timezone
from pathlib import Path
VERSION="1.5.0"

def load(p,default):
    q=Path(p); return json.loads(q.read_text("utf-8")) if q.exists() else default
def aliases(groups):
    out={}
    for g in groups:
        names=g if isinstance(g,list) else g.get("names",[]); canonical=(g.get("canonical") if isinstance(g,dict) else names[0] if names else "")
        for n in names: out[n]=canonical
    return out
def apply_manual(dishes, ingredients, manual):
    ingredient_repl=manual.get("ingredient_name_replacements",{})
    dish_repl=manual.get("dish_name_replacements",{})
    for old,new in ingredient_repl.items():
        if old in ingredients:
            row=ingredients.pop(old); row["name"]=new; ingredients[new]={**ingredients.get(new,{}),**row}
        for row in dishes.values(): row["ingredients"]=[new if x==old else x for x in row.get("ingredients",[])]
    for old,new in dish_repl.items():
        if old in dishes:
            row=dishes.pop(old); row["name"]=new; dishes[new]={**dishes.get(new,{}),**row}
    for name,row in manual.get("ingredients",{}).items():
        ingredients[name]={**ingredients.get(name,{"name":name,"processing_methods":[],"notes":[],"sources":[]}),**row,"name":name,"manual":True}
    for name,row in manual.get("dishes",{}).items():
        dishes[name]={**dishes.get(name,{"name":name,"ingredients":[],"special_tools":[],"sources":[]}),**row,"name":name,"manual":True}
    return dishes,ingredients,dish_repl
def infer_dish(title, known_names, ingredient_names):
    """Conservative title-only fallback; returns (name, referenced ingredients)."""
    text=re.sub(r"<[^>]+>","",title)
    bracket=re.search(r"【([^】]+)】",text)
    text=bracket.group(1) if bracket else text
    text=re.sub(r"[!！‼️?？~～|丨｜,，。:：;；]+"," ",text).strip()
    for name in sorted(known_names,key=len,reverse=True):
        if name in text: return name, None
    text=re.split(r"(?:超详细|保姆级|教程|配方|做法|怎么做|这样做|学会|出摊|安排上|太香了|绝了|厨房小白|精准比例)",text,1)[0].strip()
    if "的" in text and re.search(r"(?:好吃|简单|有手|流泪|馋|必吃)",text): text=text.rsplit("的",1)[-1]
    text=re.sub(r"^(?:广\s*|最近很火的|以前也不知道|在家做出饭店水准的|吃上一口真是人间值得了|夏日美食|酸甜爽口|不一样的|可以当零食的|好吃到\S+|简单到\S+|今天做|教你做|来做一道)+","",text).strip()
    text=re.sub(r"怎么能.*$|(?:竟然)?这么好吃.*$|相当好吃.*$|太好吃了.*$|又很简单.*$|免油炸.*$|来了.*$","",text).strip()
    text=re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]","",text)
    tail=re.search(r"([\u4e00-\u9fff]{2,10}(?:炒饭|拌饭|捞饭|盖饭|拌面|冷面|烩面|焖面|汤|羹|粥|饼|包子|饺子|鸡架|排骨|豆腐|茄子|菜心|黄瓜|辣椒油|鸡|鸭|鱼|虾|蟹|肉))$",text)
    if tail: text=tail.group(1)
    if not (2 <= len(text) <= 16): return None, None
    # Precision first: promotional residue means the boundary is uncertain.
    if re.search(r"分钟|搞定|下饭|一口|不用|饭店|营养|均衡|吃着|好喝|久等|朋友|谁能|味蕾|配上|一定要|火遍|全网|灵魂|定量|嘎嘣|浓郁|丝滑|绝顶|惊艳",text): return None, None
    refs=sorted({x for x in ingredient_names if len(x)>=2 and x in text})
    food_hint=bool(refs or re.search(r"(?:鸡|鸭|鹅|鱼|虾|蟹|肉|排骨|面|饭|饼|汤|羹|粥|菜|蛋|豆腐|炒|炖|蒸|煮|烤|煎|炸|拌|烧|卤|焖)$",text))
    return (text,refs) if food_hint else (None,None)
def main():
    raw=load("村驴/raw.json",{"videos":[]}); dishes=load("base/dishes.json",{}); dishes={k:v for k,v in dishes.items() if not v.get("auto_generated")}; ingredient_table=load("base/ingredients.json",{}); manual=load("manual/overrides.json",{}); dishes,ingredient_table,dish_repl=apply_manual(dishes,ingredient_table,manual); amap=aliases(load("base/dish_alias_groups.json",[]))
    candidates=sorted(set(dishes)|set(amap),key=len,reverse=True); output=[]
    for v in raw.get("videos",[]):
        hay=(v.get("title","")+"\n"+v.get("description","")).lower()
        matched=[]
        for name in candidates:
            if name.lower() in hay:
                canonical=amap.get(name,name)
                if canonical in dishes and canonical not in matched: matched.append(canonical)
        # Requested fallback: in “的xxx‼️”, xxx is a dish candidate.
        if not matched:
            hits=re.findall(r"的([^‼！!】]{2,16})[‼！!]",v.get("title",""))
            if hits:
                inferred=re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]","",hits[-1]).strip()
                hay=inferred+" "+v.get("title","")+" "+v.get("description","")
                refs=sorted({x for x in ingredient_table if len(x)>=2 and x in hay})
                if 2 <= len(inferred) <= 16:
                    if inferred not in dishes: dishes[inferred]={"name":inferred,"ingredients":refs,"special_tools":[],"sources":[f"bilibili:{v.get('bvid','')}"],"auto_generated":True,"needs_review":True,"recognition_rule":"的xxx‼️"}
                    matched=[inferred]
        if not matched:
            inferred, refs=infer_dish(v.get("title","")+" "+v.get("description",""),set(dishes)|set(amap),set(ingredient_table))
            if inferred:
                if inferred not in dishes:
                    dishes[inferred]={"name":inferred,"ingredients":refs or [],"special_tools":[],"sources":[f"bilibili:{v.get('bvid','')}"],"auto_generated":True,"needs_review":True}
                matched=[inferred]
        if v.get("bvid") in manual.get("video_dishes",{}): matched=manual["video_dishes"][v["bvid"]]
        matched=[dish_repl.get(x,x) for x in matched]
        item=dict(v); item["数据标记程序版本号"]=VERSION; item["菜名"]=matched; output.append(item)
    out={"schema_version":1,"labeler_version":VERSION,"generated_at":datetime.now(timezone.utc).isoformat(),"videos":output}
    Path("村驴/videos.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n","utf-8")
    Path("base/dishes.json").write_text(json.dumps(dict(sorted(dishes.items())),ensure_ascii=False,indent=2)+"\n","utf-8")
    Path("base/ingredients.json").write_text(json.dumps(dict(sorted(ingredient_table.items())),ensure_ascii=False,indent=2)+"\n","utf-8")
    print(f"labeled={len(output)} version={VERSION}")
if __name__=="__main__": main()
