import json
from pathlib import Path


path = Path("config.json")
config = json.loads(path.read_text(encoding="utf-8"))
for project in config.get("projects", []):
    project["owner"] = "demo"
path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
print("projects-assigned")
