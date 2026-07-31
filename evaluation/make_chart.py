from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


data_path = Path("evaluation/times.csv")
output_path = Path("evaluation/task_time_comparison.pdf")

plt.rcParams["font.family"] = "Hiragino Kaku Gothic ProN"
plt.rcParams["axes.unicode_minus"] = False

data = pd.read_csv(data_path)

if data["time_seconds"].isna().any():
    raise ValueError("time_seconds に空白があります。")

summary = (
    data.groupby(["task", "method"])["time_seconds"]
    .mean()
    .unstack()
)

ax = summary.plot(kind="bar", figsize=(10, 5.5))

ax.set_title("ExcelとJob Trackerの作業時間比較")
ax.set_xlabel("作業")
ax.set_ylabel("平均時間（秒）")
ax.tick_params(axis="x", rotation=15)
ax.legend(title="方法")

plt.tight_layout()
plt.savefig(output_path, format="pdf")
plt.close()

print(f"グラフを作成しました: {output_path}")
print(summary)
