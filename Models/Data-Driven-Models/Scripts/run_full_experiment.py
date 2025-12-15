"""Legacy convenience runner that sequences feature creation, splitting,
training, evaluation, and reporting for 1/2/3-day horizons. Update the command
list as needed, then execute once to reproduce the entire classical pipeline in
a single shot."""

import subprocess
import time

print("🚀 STARTING FULL 1-2-3 DAY EXPERIMENT")

for days in [1, 2, 3]:
    print(f"\n\n>>> PROCESSING {days}-DAY LEAD TIME <<<")

    steps = [
        f"python Models/Data-Driven-Models/Scripts/04_create_features.py --days {days}",
        f"python Models/Data-Driven-Models/Scripts/05_train_test_split.py --days {days}",
        f"python Models/Data-Driven-Models/Scripts/06_train_models.py --days {days}",
        f"python Models/Data-Driven-Models/Scripts/07_evaluate_test.py --days {days}"
    ]

    for cmd in steps:
        subprocess.run(cmd, shell=True, check=True)

# Finally, generate summary
subprocess.run("python Models/Data-Driven-Models/Scripts/08_global_summary.py", shell=True, check=True)
subprocess.run("python Models/Data-Driven-Models/Scripts/09_visualize_results.py", shell=True, check=True)

print("\n✅ EXPERIMENT COMPLETE.")