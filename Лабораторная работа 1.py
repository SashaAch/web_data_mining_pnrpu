import requests
from bs4 import BeautifulSoup
import networkx as nx
from rutermextract import TermExtractor
import plotly.graph_objects as go

URL = "https://ru.wikipedia.org/wiki/Категория:Горнодобывающие_компании_России"

def get_companies_from_wikipedia(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Находим div с указанными атрибутами
    content_div = soup.find('div', {'lang': 'ru', 'dir': 'ltr', 'class': 'mw-content-ltr'})

    if not content_div:
        return []

    # Извлекаем все ссылки внутри найденного div
    links = content_div.find_all('a')
    companies = [link.get_text() for link in links if link.get('href').startswith("/wiki/")]

    return companies

companies = get_companies_from_wikipedia(URL)
print(companies)




BASE_URL = "https://ru.wikipedia.org"
term_extractor = TermExtractor()

def get_wikipedia_content(page_name):
    url = f"{BASE_URL}/wiki/{page_name}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    content_div = soup.find('div', {'id': 'mw-content-text'})
    return content_div.get_text() if content_div else ""

# Создаем граф
G = nx.DiGraph()

# Сбор данных и ключевых слов
data_dict = {}
for company in companies[:25]:  # Ограничимся 25 компаниями для простоты
    content = get_wikipedia_content(company)
    terms = [term.normalized for term in term_extractor(content)[:10]]
    data_dict[company] = {
        "content": content,
        "terms": terms
    }

# Сравниваем ключевые слова между ресурсами
for company1, data1 in data_dict.items():
    for company2, data2 in data_dict.items():
        if company1 != company2:
            common_terms = set(data1["terms"]) & set(data2["terms"])
            if common_terms:
                G.add_edge(company1, company2, terms=list(common_terms))

# Построение графа с помощью plotly
pos = nx.spring_layout(G)

edge_x = []
edge_y = []
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=0.5, color='#888'),
    hoverinfo='none',
    mode='lines')

node_x = []
node_y = []
node_adjacencies = []
node_text = []

for node in G.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)

for node, adjacencies in enumerate(G.adjacency()):
    node_adjacencies.append(len(adjacencies[1]))
    node_text.append(adjacencies[0])

node_keyword_text = []
for node in G.nodes():
    node_keyword_text.append(', '.join(data_dict[node]['terms']))

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers+text',
    hoverinfo='text',
    textposition='top center',
    text=node_text,  # Отображаем названия компаний рядом с маркерами
    hovertext=node_keyword_text,  # Отображаем ключевые слова при наведении курсора
    marker=dict(
        showscale=True,
        size=10,
        colorbar=dict(
            thickness=15,
            title='Node Connections',
            xanchor='left',
            titleside='right'
        ),
        line_width=2))

node_trace.marker.color = node_adjacencies

fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title='Network of Companies based on shared terms',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0, l=0, r=0, t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )

fig.show()


