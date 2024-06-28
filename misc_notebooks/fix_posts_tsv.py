import pandas as pd

# Load the TSV file
df = pd.read_csv('posts.tsv', sep='\t')
df["Post ID"] = range(1, len(df) + 1)
df.to_csv('posts.tsv', sep='\t', index=False)