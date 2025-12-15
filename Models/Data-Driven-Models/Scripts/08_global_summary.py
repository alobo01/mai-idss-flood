import pandas as pd
import glob
import os

print("=" * 70)
print("GENERATING GLOBAL SUMMARY TABLE")
print("=" * 70)

# Find all scorecards
files = glob.glob("./L*d/scorecard.csv")
if not files:
    print("❌ No scorecards found. Run the pipeline first.")
    exit()

all_results = []
for f in files:
    all_results.append(pd.read_csv(f))

# Combine
final_df = pd.concat(all_results, ignore_index=True)

# Sort logic: Lead Time -> Model Name
final_df = final_df.sort_values(['Lead Time', 'Model'])

# Save
os.makedirs("Models/Data-Driven-Models/Results/Summary", exist_ok=True)
final_df.to_csv("Models/Data-Driven-Models/Results/Summary/global_comparison.csv", index=False)

print("\nGLOBAL RESULTS TABLE:")
print(final_df.to_string(index=False))
print(f"\n  ✓ Saved to Models/Data-Driven-Models/Results/Summary/global_comparison.csv")