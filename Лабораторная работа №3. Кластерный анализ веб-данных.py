import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import requests
from bs4 import BeautifulSoup
import re
import urllib
import matplotlib
matplotlib.use('Agg')

# Список блюд для поиска упоминаний
dishes = [
    "Пицца", "Бургеры", "Стейки", "Салаты", "Супы", "Блюда на гриле",
    "Пельмени", "Борщ", "Пирожки", "Паста", "Поке", "Рамен",
    "Вок", "Том-Ям", "Шашлык", "Хинкали", "Хачапури", "Суши"
]


def process_article(url, dish_mentions):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve article {url}")
        return dish_mentions

    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text()

    for dish in dishes:
        dish_mentions[dish] += len(re.findall(dish, text, re.IGNORECASE))

    return dish_mentions


def process_page(base_url, page_url, dish_mentions):
    response = requests.get(page_url)
    if response.status_code != 200:
        print(f"Failed to retrieve page {page_url}")
        return dish_mentions

    soup = BeautifulSoup(response.content, 'html.parser')
    article_links = [a['href'] for a in soup.find_all('a', href=True) if '/food/' in a['href'] and '/comments/' not in a['href']]

    for article_url in set(article_links):
        print(article_url)
        if not article_url.startswith(('http:', 'https:')):

            article_url = urllib.parse.urljoin(base_url, article_url)

        dish_mentions = process_article(article_url, dish_mentions)

    return dish_mentions


def process_city(base_url, city, all_mentions):
    dish_mentions = {dish: 0 for dish in dishes}

    for page_num in range(1, 11):  # проверим первые 10 страниц
        print(f"Processing {base_url}&page={page_num} for {city}")
        page_url = f"{base_url}&page={page_num}"
        dish_mentions = process_page(base_url, page_url, dish_mentions)

    all_mentions[city] = dish_mentions


def process_all_cities(urls):
    all_mentions = {}

    for base_url, city in urls:
        process_city(base_url, city, all_mentions)
        print(f'{city}: {all_mentions[city]}')

    file_name = 'all_dish_mentions.json'
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(all_mentions, f, ensure_ascii=False, indent=4)

    print(f'Data saved to {file_name}')

def load_data(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_top_dish(df):
    return df.idxmax(axis=1)

def cluster_cities(df, n_clusters=3):
    kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=10).fit(df)

    df['Cluster'] = kmeans.labels_

    print(df['Cluster'].value_counts())
    return df

def visualize_clusters(df, city_names):
    pca = PCA(n_components=2)
    df_pca = pca.fit_transform(df.drop('Cluster', axis=1))
    df_pca = pd.DataFrame(df_pca, columns=['PC1', 'PC2'])
    df_pca['Cluster'] = df['Cluster'].values
    df_pca['City'] = city_names

    plt.figure(figsize=(10, 8))
    sns.scatterplot(data=df_pca, x='PC1', y='PC2', hue='Cluster', palette='Set2', s=100)

    # добавляем имена городов на график
    for i in range(len(df_pca)):
        plt.text(df_pca.PC1[i], df_pca.PC2[i], df_pca.City[i], fontsize=10)

    plt.title('Clusters of Cities Based on Dish Preferences')
    plt.savefig('clusters.png')

def analyze_data(all_mentions):
    df = pd.DataFrame(all_mentions).T
    city_names = df.index
    df = cluster_cities(df)
    visualize_clusters(df, city_names)

    top_dish = get_top_dish(df.drop('Cluster', axis=1))
    print(f'Top dish in each city:\n{top_dish}')

def main():
    urls = [
        ("https://59.ru/text/?rubric=food", "Perm"),
        ("https://ufa1.ru/text/?rubric=food", "Ufa"),
        ("https://74.ru/text/?rubric=food", "Chelyabinsk"),
        ("https://sochi1.ru/text/?rubric=food", "Sochi"),
        ("https://ircity.ru/text/?rubric=food", "Irkutsk"),
        ("https://www.e1.ru/text/?rubric=food", "Ekaterinburg"),
        ("https://msk1.ru/text/?rubric=food", "Moscow")
    ]

    process_all_cities(urls)

    file_name = 'all_dish_mentions.json'
    all_mentions = load_data(file_name)
    analyze_data(all_mentions)


if __name__ == "__main__":
    main()