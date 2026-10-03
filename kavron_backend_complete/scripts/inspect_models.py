from pathlib import Path
import json
from app.core.config import get_settings
from app.ai.registry import ModelRegistry

s=get_settings(); reg=ModelRegistry(s.model_dir,s.device)
print("Discovered models:")
for k,v in reg.discover().items(): print(f"- {k}: {v['path']}")
print("\nLoadable metadata requires ultralytics to be installed.\n")
for mid, fn in [("general",s.general_model),("person",s.person_model),("pose",s.pose_model),("specialist",s.specialist_model),("pose_alt",s.pose_alt_model)]:
    try:
        reg.load(mid,fn); print(json.dumps(reg.metadata(mid),default=str,indent=2))
    except Exception as exc:
        print(f"{mid}: {exc}")
