# Efficacy Tool Quick-Start Examples

This guide provides sample commands for running the `calculate_efficacy.py` script in both single and bulk modes.

## 1. Single Dataset Evaluation
Use this command to compare a single agent-generated folder against a reviewed gold standard.

### Sample Command
```bash
python3 tools/agent_efficacy/calculate_efficacy.py \
  --test /usr/local/google/home/nehil/datacommons/import/git/data/test_DESA-GENDER_2025_OBS_ICT_SKILL_RT \
  --gold /usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/output/reviewed_pvmap_harish/DESA-GENDER_2025_OBS_ICT_SKILL_RT \
  --output /usr/local/google/home/nehil/datacommons/import/git/data/tmp/efficacy_results/single_run \
  --dataset_id ICT_SKILL_RT
```

### Result
- Dashboard: `/tmp/efficacy_results/single_run/Agent_Efficacy_Board.html`
- Updates: Precision, Recall, and F1 will be correctly populated in the HTML.

---

## 2. Bulk Evaluation (Multiple Datasets)
Use this command to evaluate all datasets in a directory. It will create a unique, timestamped folder for the run.

### Sample Command
```bash
python3 tools/agent_efficacy/calculate_efficacy.py \
  --bulk \
  --test /usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/output/agent_predictions \
  --gold /usr/local/google/home/nehil/datacommons/import/git/data/undata/DESA/output/reviewed_pvmap_harish \
  --output /tmp/efficacy_results/bulk_runs
```

### Result
- Output Directory: `/tmp/efficacy_results/bulk_runs/bulk_run_20260602_HHMMSS/`
- Summary File: `summary.csv` inside the new run folder.
- Dashboards: Individual `Agent_Efficacy_Board.html` files for every dataset found.

---

## 3. How to Present Results
1. **HTML Dashboard:** Open the `Agent_Efficacy_Board.html` file in any browser to view the "Hero Metrics" and detailed semantic diffs.
2. **Summary CSV:** Use the `summary.csv` generated during bulk runs to create a high-level report or table of performance across all indicators.
