import networkx as nx
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pyvis
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict
from ast import literal_eval
import textwrap
import graphviz
import pygraphviz
from pyvis.network import Network
import numpy as np
from sklearn.manifold import TSNE
import plotly.express as px
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import spacy


DF = pd.read_csv('posts.tsv')
NODE_COLOR = {'keyword': 'lightgreen', 'title': 'skyblue'}


# create word list from posts
nlp = spacy.load('en_core_web_sm')
words = []
for i, row in DF.iterrows():
    words.append(row["Keywords"])

documents = [TaggedDocument(doc, [i]) for i, doc in enumerate(words)]
model = Doc2Vec(documents, vector_size=5, window=2, min_count=1, workers=4)

# plot the t-SNE of the embeddings of the descriptions
X = np.array([model.infer_vector(words[i]) for i in range(len(words))])
X_embedded = TSNE(n_components=2).fit_transform(X)


def get_closest_df(
    title: dict,
    n_closest: int = 5,
) -> pd.DataFrame:
    """

    """
    idx = DF[DF['Title'] == title].index[0]
    x = X_embedded[idx]
    distances = np.linalg.norm(X_embedded - x, axis=1)
    closest = distances.argsort()[1:n_closest]

    # plot the n_closest on t-SNE
    fig = px.scatter(x=X_embedded[:,0], y=X_embedded[:,1], hover_name=DF['Title'],
                     color=np.where(np.any(np.arange(len(words)) == closest.reshape(-1, 1), axis=0), f'{n_closest} closest', 'others'))
    fig.update_traces(textposition='top center')
    fig.update_layout(title='t-SNE of the embeddings of the descriptions')
    fig.show()

    return DF.iloc[closest]


def get_closest_posts_plot_html(
    post: dict,
) -> str:
    """
    post = {
        'title'
        'description'
        'keywords'
        'dataset_type'
        'collection_period'
        'organism'
        'genes'
        'tissue_celltype'
        'condition'
        'technique'
        'instrument_platform'
        'software'
        'usage_restrictions'
        'related_datasets'
        'link'
        'filename'
        'user'
        'id'
        'likes'
    }
    """
    G = nx.Graph()
    attributes = defaultdict(list)
    closest_df = get_closest_df(post)
    for index, row in closest_df.iterrows():
        title = row['Title']
        keywords = str(row['Keywords']).split(" ")
        for keyword in keywords:
            attributes[keyword].append(title)
    attributes = {key: list(set(value)) for key, value in attributes.items()}
    attributes = {key: value for key, value in attributes.items() if len(value) >= 2}
    for keyword in attributes.keys():
        G.add_node(keyword, type='keyword')
    for title in set(element for sublist in attributes.values() for element in sublist):
        wrapped_title = textwrap.fill(title, width=20)
        G.add_node(wrapped_title, type='title')
    for keyword, related_titles in attributes.items():
        for title in related_titles:
            wrapped_title = textwrap.fill(title, width=20)
            G.add_edge(wrapped_title, keyword)
    # Draw the graph
    pos = nx.nx_agraph.graphviz_layout(G, "sfdp")
    #plt.figure(figsize=(40, 40))
    node_size = {'keyword': 10, 'title': 15}
    # Assign node attributes for color and size
    for node, data in G.nodes(data=True):
        node_type = data['type']
        G.nodes[node]['color'] = NODE_COLOR[node_type]
        G.nodes[node]['size'] = node_size[node_type]
    g = Network(height = 800, width = 1500, notebook = True)
    g.barnes_hut()
    for node, data in G.nodes(data=True):
        if data['type'] == 'title':
            g.add_node(node, size=60, color='skyblue', font={'size': 40})
        elif data['type'] == 'keyword':
            g.add_node(node, size=80, color='lightgreen', font={'size': 100})
    for edge in G.edges():
        g.add_edge(edge[0], edge[1], width=12)
    html_code = g.get_html()
    return html_code
