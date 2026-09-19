#!/usr/bin/env python3
"""Download the auditable recipe corpus from HowToCook into one text file."""
import base64, json, os, time
from pathlib import Path
import requests

API="https://api.github.com/repos/Anduin2017/HowToCook"
HEAD={"Accept":"application/vnd.github+json","User-Agent":"cook-videos-reference-builder"}
if os.getenv("GITHUB_TOKEN"): HEAD["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]

def get(url):
    r=requests.get(url,headers=HEAD,timeout=30); r.raise_for_status(); return r.json()

def main():
    repo=get(API); branch=repo["default_branch"]
    tree=get(f"{API}/git/trees/{branch}?recursive=1")["tree"]
    paths=sorted(x["path"] for x in tree if x["type"]=="blob" and x["path"].startswith("dishes/") and x["path"].endswith(".md"))
    chunks=["# Generated reference corpus","# Source: https://github.com/Anduin2017/HowToCook",f"# Revision: {branch}",""]
    for i,path in enumerate(paths):
        obj=get(f"{API}/contents/{path}?ref={branch}")
        text=base64.b64decode(obj["content"]).decode("utf-8","replace")
        chunks += [f"===== FILE: {path} =====",text.strip(),""]
        if i and i%40==0: time.sleep(1)
    Path("reference").mkdir(exist_ok=True); Path("reference/howtocook-recipes.txt").write_text("\n".join(chunks)+"\n","utf-8")
    print(f"recipes={len(paths)}")
if __name__=="__main__": main()

