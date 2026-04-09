import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

df = pd.read_csv("load_benchmark.csv")
sns.lineplot(df, x='num_cpus', y='time_s', hue='type', style='dataset', palette='Dark2')

df['speedup'] = df[['dataset', 'time_s']].groupby('dataset').transform('mean')['time_s'] / df['time_s']

#ax = plt.gca()
#ax.set_yscale('log', base=2)
from IPython import embed
embed(colors='linux')
