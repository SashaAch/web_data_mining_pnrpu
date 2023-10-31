from comcrawl import IndexClient

client = IndexClient()

# Поиск информации на главных страницах интересующих сайтов
sites = [
    # "59.ru",
    "pstu.ru"
]

data = {}

for site in sites:
    client.search(f"{site}/*")
    client.download()

    # Ограничиваем до 3 записей
    data[site] = client.results[:3]

    print(data)

mentions = {}
for site, results in data.items():
    count = sum(page['html'].count("ИТАС") for page in results)
    mentions[site] = count

import matplotlib.pyplot as plt

# Подготовка данных
sites = list(mentions.keys())
counts = list(mentions.values())

# Построение столбчатой диаграммы
plt.bar(sites, counts, color=['blue', 'green', 'red'])
plt.xlabel('Сайты')
plt.ylabel('Упоминания кафедры ИТАС')
plt.title('Упоминания кафедры ИТАС на сайтах')
plt.show()
