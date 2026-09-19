#!/usr/bin/env python3
"""Versioned deterministic dish labeling. Bump VERSION when rules change."""
import json, re
from datetime import datetime, timezone
from pathlib import Path
VERSION="1.0.0"

def load(p,default):
    q=Path(p); return json.loads(q.read_text("utf-8")) if q.exists() else default
def aliases(groups):
    out={}
    for g in groups:
        names=g if isinstance(g,list) else g.get("names",[]); canonical=(g.get("canonical") if isinstance(g,dict) else names[0] if names else "")
        for n in names: out[n]=canonical
    return out
def main():
    raw=load("村驴/raw.json",{"videos":[]}); dishes=load("base/dishes.json",{}); amap=aliases(load("base/dish_alias_groups.json",[]))
    candidates=sorted(set(dishes)|set(amap),key=len,reverse=True); output=[]
    for v in raw.get("videos",[]):
        hay=(v.get("title","")+"\n"+v.get("description","")).lower()
        matched=[]
        for name in candidates:
            if name.lower() in hay:
                canonical=amap.get(name,name)
                if canonical in dishes and canonical not in matched: matched.append(canonical)
        item=dict(v); item["数据标记程序版本号"]=VERSION; item["菜名"]=matched; output.append(item)
    out={"schema_version":1,"labeler_version":VERSION,"generated_at":datetime.now(timezone.utc).isoformat(),"videos":output}
    Path("村驴/videos.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n","utf-8")
    print(f"labeled={len(output)} version={VERSION}")
if __name__=="__main__": main()
