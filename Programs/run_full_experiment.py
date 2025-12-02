import subprocess
import time

print("🚀 STARTING FULL 1-2-3 DAY EXPERIMENT")

for days in [1, 2, 3]:
    print(f"\n\n>>> PROCESSING {days}-DAY LEAD TIME <<<")

    steps = [
        f"python Programs/04_create_features.py --days {days}",
        f"python Programs/05_train_test_split.py --days {days}",
        f"python Programs/07_train_models.py --days {days}",
        f"python Programs/08_evaluate_test.py --days {days}"
    ]

    for cmd in steps:
        subprocess.run(cmd, shell=True, check=True)

# Finally, generate summary
subprocess.run("python Programs/09_global_summary.py", shell=True, check=True)
subprocess.run("python Programs/10_visualize_results.py", shell=True, check=True)

print("\n✅ EXPERIMENT COMPLETE.")