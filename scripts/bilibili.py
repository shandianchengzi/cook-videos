#!/usr/bin/env python3
"""Incrementally collect public metadata for one Bilibili creator."""
from __future__ import annotations
import argparse, hashlib, json, os, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
import requests

MID = 417298480
MIXIN = [46,47,18,2,53,8,23,32,15,50,10,31,58,3,45,35,27,43,5,49,33,9,42,19,29,28,14,39,12,38,41,13,37,48,7,16,24,55,40,61,26,17,0,1,60,51,30,4,22,25,54,21,56,59,6,63,57,62,11,36,20,34,44,52]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36 cook-videos/1.0"

class Bili:
    def __init__(self):
        self.s = requests.Session(); self.s.headers.update({"User-Agent": UA, "Referer": f"https://space.bilibili.com/{MID}/video"})
        if os.getenv("BILIBILI_COOKIE"): self.s.headers["Cookie"] = os.environ["BILIBILI_COOKIE"]
        self.key = None
    def get(self, url, params=None):
        r=self.s.get(url, params=params, timeout=25); r.raise_for_status(); data=r.json()
        if data.get("code") != 0: raise RuntimeError(f"Bilibili API {data.get('code')}: {data.get('message')}")
        return data["data"]
    def wbi(self, params):
        if not self.key:
            nav=self.get("https://api.bilibili.com/x/web-interface/nav")["wbi_img"]
            raw=nav["img_url"].rsplit("/",1)[-1].split(".")[0]+nav["sub_url"].rsplit("/",1)[-1].split(".")[0]
            self.key="".join(raw[i] for i in MIXIN)[:32]
        p={**params,"wts":int(time.time())}; p={k:re.sub(r"[!'()*]", "", str(v)) for k,v in p.items()}
        query=urlencode(sorted(p.items())); p["w_rid"]=hashlib.md5((query+self.key).encode()).hexdigest(); return p
    def page(self, pn, ps=50):
        return self.get("https://api.bilibili.com/x/space/wbi/arc/search", self.wbi({"mid":MID,"pn":pn,"ps":ps,"order":"pubdate"}))
    def detail(self, bvid): return self.get("https://api.bilibili.com/x/web-interface/view", {"bvid":bvid})

def normalize(d):
    return {"aid":d.get("aid"),"bvid":d.get("bvid"),"title":d.get("title",""),"description":d.get("desc",""),
      "cover_url":d.get("pic",""),"duration":d.get("duration",0),"published_at":d.get("pubdate",0),
      "created_at":d.get("ctime",0),"owner":d.get("owner",{}),"stat":d.get("stat",{}),"pages":d.get("pages",[]),
      "copyright":d.get("copyright"),"tid":d.get("tid"),"tname":d.get("tname"),"dynamic":d.get("dynamic","")}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="村驴/raw.json"); ap.add_argument("--full",action="store_true"); a=ap.parse_args()
    path=Path(a.output); old=json.loads(path.read_text("utf-8")) if path.exists() else {"videos":[]}
    known={v["bvid"]:v for v in old.get("videos",[]) if v.get("bvid")}; api=Bili(); found={}; pn=1
    while True:
        page=api.page(pn); items=page.get("list",{}).get("vlist",[])
        if not items: break
        unseen=0
        for item in items:
            bv=item.get("bvid")
            if bv in known and not a.full: continue
            found[bv]=normalize(api.detail(bv)); unseen+=1; time.sleep(.35)
        if not a.full and unseen==0: break
        if pn*50 >= int(page.get("page",{}).get("count",0)): break
        pn+=1; time.sleep(1)
    merged={**known,**found}; videos=sorted(merged.values(),key=lambda x:(x.get("published_at",0),x.get("bvid","")),reverse=True)
    out={"schema_version":1,"source":{"platform":"bilibili","mid":MID,"name":"村驴"},"crawled_at":datetime.now(timezone.utc).isoformat(),"videos":videos}
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n","utf-8")
    print(f"new={len(found)} total={len(videos)}")
if __name__ == "__main__": main()

