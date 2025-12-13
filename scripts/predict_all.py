#!/usr/bin/env python3
"""
This script has been moved to `database/scripts/predict_all.py`.
Please run the script from that path. This file is kept for backward compatibility and
will raise an informational message.
"""
import sys
import os
from pathlib import Path

print("This script has moved to 'database/scripts/predict_all.py'. Please run that file instead.")
sys.exit(1)
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
