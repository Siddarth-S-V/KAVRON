from __future__ import annotations
import asyncio, uuid, time
from app.events.rules import bottom_center, point_in_polygon

class EventEngine:
    def __init__(self, runtime_state, publish):
        self.state=runtime_state; self.publish=publish; self.fences=[]; self.cooldowns={}
    def set_fences(self, fences): self.fences=fences
    async def handle_detection(self, event: dict):
        for fence in self.fences:
            if not fence.get("active", True) or fence.get("camera_id") != event.get("camera_id"): continue
            allowed=fence.get("allowed_objects") or []
            if allowed and event.get("class_name") not in allowed: continue
            if fence.get("geometry_type") != "polygon": continue
            if not point_in_polygon(bottom_center(event["bbox"]), fence.get("coordinates", [])): continue
            key=f"{event['camera_id']}:{event.get('track_id')}:{fence['id']}"
            now=time.time()
            if now-self.cooldowns.get(key,0)<8: continue
            self.cooldowns[key]=now
            alert={
                "event_id":f"EVT-{uuid.uuid4().hex[:10].upper()}",
                "type":"intrusion",
                "event_type":"INTRUSION",
                "severity":fence.get("severity","HIGH"),
                "camera_id":event["camera_id"],
                "track_id":event.get("track_id"),
                "confidence":event.get("confidence",0),
                "class_name":event.get("class_name"),
                "fence_id":fence["id"],
                "timestamp":event.get("timestamp"),
            }
            self.state.add_alert(alert)
            await self.publish(alert)
