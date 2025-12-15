#!/usr/bin/env python3
"""
UI-side database script to run historical predictions using the backend prediction service.
It writes a status JSON to `UI/scripts/predict_all_status.json` to allow external monitoring.

Usage:
  micromamba activate idss && python UI/scripts/predict_all.py --lead-times 1,2,3 --skip-cached

Note: This must be run from the repository root.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STATUS_FILE = os.path.join(REPO_ROOT, 'UI', 'scripts', 'predict_all_status.json')


def write_status(status: dict):
    try:
        with open(STATUS_FILE, 'w') as fh:
            json.dump(status, fh, indent=2)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description='Run historical prediction job and write progress status')
    parser.add_argument('--lead-times', default='1,2,3', help='Comma-separated lead times (e.g., 1,2,3)')
    parser.add_argument('--skip-cached', action='store_true', help='Skip cached predictions')
    args = parser.parse_args()

    lead_time_list = [int(x.strip()) for x in args.lead_times.split(',') if x.strip()]
    skip_cached = args.skip_cached

    # update sys.path to import backend modules
    sys.path.insert(0, os.path.join(REPO_ROOT, 'UI', 'backend'))
    try:
        from app import prediction_service
    except Exception as e:
        write_status({'status': 'failed', 'message': f'Import failed: {e}', 'updated_at': datetime.now().isoformat()})
        raise

    # Write initial status
    write_status({'status': 'starting', 'lead_times': lead_time_list, 'skip_cached': skip_cached, 'started_at': datetime.now().isoformat()})

    start_ts = time.time()

    def on_progress(p):
        status = {
            'status': 'running',
            'message': p.get('message'),
            'percent': p.get('percent'),
            'completed': p.get('completed'),
            'total': p.get('total'),
            'eta_seconds': p.get('eta_seconds'),
            'updated_at': datetime.now().isoformat(),
        }
        write_status(status)
        print(f"Progress: {status['percent']}% ({status['completed']}/{status['total']}) ETA: {status['eta_seconds']}s")

    try:
        result = prediction_service.predict_all_historical(lead_times=lead_time_list, skip_cached=skip_cached, on_progress=on_progress)
        write_status({'status': 'completed', 'result_summary': {'total_predictions': result.get('total_predictions')}, 'completed_at': datetime.now().isoformat()})
        print('Completed. Predictions generated:', result.get('total_predictions'))
    except Exception as e:
        write_status({'status': 'failed', 'message': str(e), 'error': True, 'updated_at': datetime.now().isoformat()})
        raise


if __name__ == '__main__':
    main()
