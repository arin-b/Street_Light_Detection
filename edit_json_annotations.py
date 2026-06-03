import json

json_file = "/media/arindamb/NewVolume/RBCCPS-Internship-Docs/annotations_LLM/annotations_LLM\\batch_004\\annotation_llm.json"

# Load JSON
with open(json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Remove unwanted fields from each annotation
for ann in data.get("annotations", []):
    ann.pop("confounder_boxes", None)
    ann.pop("polygons", None)
    ann.pop("measurement", None)

# Save back to the same file
with open(json_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Done. Removed confounder_boxes, polygons, and measurement fields.")