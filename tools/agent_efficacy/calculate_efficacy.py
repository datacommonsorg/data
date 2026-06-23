import os
import sys
import re
import csv
import argparse
import datetime

# Set up paths to import tools
PROJECT_ROOT = '/usr/local/google/home/nehil/datacommons/import/git/data'
sys.path.append(os.path.join(PROJECT_ROOT, 'tools/statvar_importer'))
sys.path.append(os.path.join(PROJECT_ROOT, 'util'))
sys.path.append(os.path.join(PROJECT_ROOT, 'tools/agentic_import/metrics'))

import mcf_diff
from counters import Counters
from property_value_mapper import PropertyValueMapper
from pvmap_generator_metrics import PVMapGeneratorMetricsRunner

def get_metrics_from_counters(counters_obj):
    # Use metrics formula directly from pvmap_generator_metrics.py
    diff_stats = {'counters': counters_obj.get_counters()}
    stats = PVMapGeneratorMetricsRunner.get_stats_from_diff_counters(None, diff_stats)
    
    return {
        'tp': stats.get('true_positive', 0), 
        'fp': stats.get('false_positive', 0), 
        'fn': stats.get('false_negative', 0),
        'precision': stats.get('precision', 0), 
        'recall': stats.get('recall', 0), 
        'f1': stats.get('f1', 0)
    }

def load_pv_map_nodes(file_path):
    """Loads PV map into MCF-like nodes using PropertyValueMapper normalization."""
    pv_mapper = PropertyValueMapper()
    pv_mapper.load_pvs_from_file(file_path)
    # Get the raw GLOBAL map
    raw_map = pv_mapper.get_pv_map().get('GLOBAL', {})
    # Convert to standard node format: {dcid: {prop: val}}
    nodes = {}
    for key, pvs in raw_map.items():
        # Ensure DCID is clean
        nodes[key] = pvs
    return nodes

def run_comparison(pred_path, gold_path, is_pvmap=False, use_fingerprint=False):
    if not os.path.exists(pred_path) or not os.path.exists(gold_path):
        print(f"Skipping: missing {pred_path} or {gold_path}")
        return "", {'tp': 0, 'fp': 0, 'fn': 0, 'precision': 0, 'recall': 0, 'f1': 0}

    counters = Counters()
    config = {
        'show_diff_nodes_only': True,
        'ignore_property': ['description', 'provenance', 'memberOf', 'member', 'name', 'constraintProperties', 'keyString', 'relevantVariable'],
        'fingerprint_dcid': use_fingerprint
    }

    if is_pvmap:
        # Specialized loading for PV Maps to handle wide vs narrow formats
        nodes1 = load_pv_map_nodes(pred_path)
        nodes2 = load_pv_map_nodes(gold_path)
        print(f"  [PVMap] Loaded {len(nodes1)} nodes from pred, {len(nodes2)} from gold")
        diff_text = mcf_diff.diff_mcf_nodes(nodes1, nodes2, config, counters)
    else:
        # Standard MCF loading
        diff_text = mcf_diff.diff_mcf_files(pred_path, gold_path, config, counters)
    
    metrics = get_metrics_from_counters(counters)
    return diff_text, metrics

def run_csv_comparison(pred_path, gold_path):
    if not os.path.exists(pred_path) or not os.path.exists(gold_path):
        print(f"Skipping: missing {pred_path} or {gold_path}")
        return "Missing files.", {'tp': 0, 'fp': 0, 'fn': 0, 'precision': 0, 'recall': 0, 'f1': 0}

    def load_csv(path):
        rows = set()
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header
            next(reader, None)
            for row in reader:
                clean_row = tuple(cell.strip() for cell in row if cell.strip())
                if clean_row:
                    rows.add(clean_row)
        return rows

    pred_rows = load_csv(pred_path)
    gold_rows = load_csv(gold_path)

    tp = len(pred_rows.intersection(gold_rows))
    fp = len(pred_rows - gold_rows)
    fn = len(gold_rows - pred_rows)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    diff_text = f"Total Prediction Rows: {len(pred_rows)}\nTotal Gold Rows: {len(gold_rows)}\nExact Matches (TP): {tp}\nOnly in Prediction (FP): {fp}\nOnly in Gold (FN): {fn}"
    
    return diff_text, {'tp': tp, 'fp': fp, 'fn': fn, 'precision': precision, 'recall': recall, 'f1': f1}

def update_html(template_content, dataset_id, hero_metrics, detailed_results):
    content = template_content
    for key, label in [('f1', 'Agent Efficacy (F1)'), ('precision', 'Precision'), ('recall', 'Recall')]:
        escaped_label = re.escape(label)
        content = re.sub(
            rf'({escaped_label}.*?tracking-tight(?:er)?">)([\d\.]+%)(</p>)',
            r'\g<1>' + f"{hero_metrics[key]*100:.1f}%" + r'\g<3>',
            content, flags=re.DOTALL
        )
    
    content = re.sub(r'(True Positives.*?tracking-tighter">)([\d,]+)(</p>)', r'\g<1>' + f"{hero_metrics['tp']:,}" + r'\g<3>', content, flags=re.DOTALL)
    content = re.sub(r'(False Positives.*?tracking-tighter">)([\d,]+)(</p>)', r'\g<1>' + f"{hero_metrics['fp']:,}" + r'\g<3>', content, flags=re.DOTALL)
    content = re.sub(r'(False Negatives.*?tracking-tighter">)([\d,]+)(</p>)', r'\g<1>' + f"{hero_metrics['fn']:,}" + r'\g<3>', content, flags=re.DOTALL)
    content = re.sub(r'Run ID: .*?</div>', f'Run ID: {dataset_id} (Rechecked)</div>', content)

    if '<section class="mt-8 px-4 sm:px-6 lg:px-8 pb-12">' in content:
        content = content.split('<section class="mt-8 px-4 sm:px-6 lg:px-8 pb-12">')[0]

    diff_sections = '<section class="mt-8 px-4 sm:px-6 lg:px-8 pb-12"><h2 class="text-2xl lg:text-3xl font-extrabold text-slate-900 mb-6">Detailed File Comparisons (Recalculated)</h2>\n'
    for label, data in detailed_results.items():
        diff_sections += f'''
        <div class="mb-10 bg-white p-6 lg:p-8 rounded-2xl shadow-lg border-2 border-slate-200">
            <h3 class="text-xl lg:text-2xl font-black mb-4 uppercase tracking-wider text-indigo-900 border-b-2 border-indigo-100 pb-2">{label}</h3>
            <div class="grid grid-cols-3 gap-4 mb-6">
                <div class="bg-emerald-50 p-4 rounded-xl border-2 border-emerald-200"><span class="block text-xs font-black uppercase tracking-widest">Precision</span><span class="text-2xl font-black">{data['metrics']['precision']*100:.1f}%</span></div>
                <div class="bg-amber-50 p-4 rounded-xl border-2 border-amber-200"><span class="block text-xs font-black uppercase tracking-widest">Recall</span><span class="text-2xl font-black">{data['metrics']['recall']*100:.1f}%</span></div>
                <div class="bg-indigo-50 p-4 rounded-xl border-2 border-indigo-200"><span class="block text-xs font-black uppercase tracking-widest">F1 Score</span><span class="text-2xl font-black">{data['metrics']['f1']*100:.1f}%</span></div>
            </div>
            <div class="text-xs font-bold text-slate-500 mb-2 font-mono uppercase tracking-widest">Structural Diff Analysis (TP: {data['metrics']['tp']} | FP: {data['metrics']['fp']} | FN: {data['metrics']['fn']})</div>
            <pre class="bg-slate-900 text-slate-100 p-6 rounded-xl overflow-auto max-h-[30rem] text-sm font-mono whitespace-pre-wrap">{data['diff'] if data['diff'] else 'No differences found.'}</pre>
        </div>
        '''
    diff_sections += '        </section>\n</body>\n</html>'
    return content + diff_sections

def process_single_dataset(dataset_dir, output_dir, dataset_id, template_content):
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    # dataset_dir is the root of the dataset (e.g. abhishek_data/Deaths_by_week_and_sex)
    file_mappings = [
        ('pvmap.csv', os.path.join(dataset_dir, 'sample_output', 'output_pvmap.csv'), os.path.join(dataset_dir, 'sample_output', 'output_pvmap_cleaned.csv'), True, False, False),
        ('stat_vars.mcf', os.path.join(dataset_dir, 'agent_output', 'output_stat_vars.mcf'), os.path.join(dataset_dir, 'final_output', 'output_stat_vars.mcf'), False, True, False),
        ('stat_vars_schema.mcf', os.path.join(dataset_dir, 'agent_output', 'output_stat_vars_schema.mcf'), os.path.join(dataset_dir, 'final_output', 'output_stat_vars_schema.mcf'), False, False, False),
        ('tmcf', os.path.join(dataset_dir, 'agent_output', 'output.tmcf'), os.path.join(dataset_dir, 'final_output', 'output.tmcf'), False, False, False),
        ('output.csv', os.path.join(dataset_dir, 'agent_output', 'output.csv'), os.path.join(dataset_dir, 'final_output', 'output.csv'), False, False, True),
    ]

    detailed_results = {}
    metrics_summary_data = []
    total_tp = 0
    total_fp = 0
    total_fn = 0

    print(f"\n--- Rechecking Efficacy for {dataset_id} ---")
    for label, pred_path, gold_path, is_pv, use_fp, is_csv in file_mappings:
        print(f"Comparing {label}...")
        if is_csv:
            diff_text, metrics = run_csv_comparison(pred_path, gold_path)
        else:
            diff_text, metrics = run_comparison(pred_path, gold_path, is_pvmap=is_pv, use_fingerprint=use_fp)
        
        detailed_results[label] = {'diff': diff_text, 'metrics': metrics}
        print(f"  Result: F1={metrics['f1']:.1%}, TP={metrics['tp']}, FP={metrics['fp']}, FN={metrics['fn']}")
        
        metrics_summary_data.append({
            'File': label,
            'F1': f"{metrics['f1']:.4f}",
            'Precision': f"{metrics['precision']:.4f}",
            'Recall': f"{metrics['recall']:.4f}",
            'TP': metrics['tp'],
            'FP': metrics['fp'],
            'FN': metrics['fn']
        })

        total_tp += metrics['tp']
        total_fp += metrics['fp']
        total_fn += metrics['fn']

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    hero_metrics = {
        'tp': total_tp,
        'fp': total_fp,
        'fn': total_fn,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }

    metrics_summary_data.append({
        'File': 'Overall',
        'F1': f"{f1:.4f}",
        'Precision': f"{precision:.4f}",
        'Recall': f"{recall:.4f}",
        'TP': total_tp,
        'FP': total_fp,
        'FN': total_fn
    })

    # Write metrics_summary.csv
    summary_csv_path = os.path.join(output_dir, 'metrics_summary.csv')
    with open(summary_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['File', 'F1', 'Precision', 'Recall', 'TP', 'FP', 'FN'])
        writer.writeheader()
        writer.writerows(metrics_summary_data)

    final_html = update_html(template_content, dataset_id, hero_metrics, detailed_results)
    
    with open(os.path.join(output_dir, 'Agent_Efficacy_Board.html'), 'w') as f: f.write(final_html)
    return hero_metrics

def main():
    parser = argparse.ArgumentParser(description="Calculate efficacy metrics.")
    parser.add_argument('--test', required=True, help="Path to the test (prediction) directory.")
    parser.add_argument('--gold', required=False, help="Path to the gold (reviewed) directory.")
    parser.add_argument('--output', required=True, help="Path to the output directory to save results.")
    parser.add_argument('--dataset_id', default="Dataset", help="Optional dataset ID for display.")
    parser.add_argument('--file_mode', action='store_true', help="If set, treats test and gold as direct file paths.")
    parser.add_argument('--bulk', action='store_true', help="If set, treats test and gold as parent directories containing multiple dataset folders.")
    args = parser.parse_args()

    template_path = os.path.join(os.path.dirname(__file__), 'Agent_Efficacy_Board.html')
    with open(template_path, 'r') as f: 
        template_content = f.read()

    if args.bulk:
        run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = os.path.join(args.output, f"bulk_run_{run_id}")
        print(f"Starting Bulk Efficacy Calculation natively... Output: {args.output}")
        summary_data = []
        if not os.path.exists(args.output):
            os.makedirs(args.output)
            
        for dataset_id in os.listdir(args.gold):
            gold_ds_dir = os.path.join(args.gold, dataset_id)
            if not os.path.isdir(gold_ds_dir):
                continue
            
            # Allow test directories to either match exactly or be prefixed with test_
            test_ds_dir = os.path.join(args.test, dataset_id)
            if not os.path.isdir(test_ds_dir):
                test_ds_dir = os.path.join(args.test, f"test_{dataset_id}")
            
            if os.path.isdir(test_ds_dir):
                out_ds_dir = os.path.join(args.output, dataset_id)
                try:
                    hero_metrics = process_single_dataset(test_ds_dir, out_ds_dir, dataset_id, template_content)
                    if hero_metrics:
                        summary_data.append({
                            'dataset_id': dataset_id,
                            'f1': hero_metrics['f1'],
                            'precision': hero_metrics['precision'],
                            'recall': hero_metrics['recall'],
                            'tp': hero_metrics['tp'],
                            'fp': hero_metrics['fp'],
                            'fn': hero_metrics['fn']
                        })
                except Exception as e:
                    print(f"Error processing {dataset_id}: {e}")
            else:
                print(f"Skipped: {dataset_id} (Matching test directory not found)")
        
        # Write summary.csv
        if summary_data:
            summary_path = os.path.join(args.output, 'summary.csv')
            with open(summary_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['dataset_id', 'f1', 'precision', 'recall', 'tp', 'fp', 'fn'])
                writer.writeheader()
                writer.writerows(summary_data)
            print(f"\nBulk run complete. Summary saved to {summary_path}")
    else:
        process_single_dataset(args.test, args.output, args.dataset_id, template_content)
        print(f"\nRecheck complete. Results saved to {args.output}")

if __name__ == "__main__":
    main()
