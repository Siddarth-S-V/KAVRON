# Stage 4 — Multimodel Fine-Tuning

1. Annotate KAVRON-specific frames.
2. Create `training/dataset.yaml` from `dataset.yaml.example`.
3. Run `python training/train_yolo_stage4.py --model yolo11n.pt --device cpu` (or a GPU device).
4. Validate and inspect `promotion_report.json`.
5. Benchmark the candidate against the production model before promotion.

The package does not claim a fine-tuned model without labeled ground truth.
