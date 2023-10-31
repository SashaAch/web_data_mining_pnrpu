import requests
import json
from bs4 import BeautifulSoup


def get_wikipedia_data(query):
	# API-запрос к Википедии
	WIKI_API_URL = "https://ru.wikipedia.org/w/api.php"

	# Получение основной страницы
	params = {
		"action": "parse",
		"page": query,
		"format": "json",
		"prop": "text|links"
	}
	response = requests.get(WIKI_API_URL, params=params)
	data = response.json()

	# Если страница не найдена
	if "error" in data:
		return {"error": "Страница не найдена"}

	parsed_data = {}
	parsed_data["title"] = query
	parsed_data["content"] = BeautifulSoup(data["parse"]["text"]["*"], "html.parser").get_text()

	# Сбор гиперссылок с полными URL-адресами
	base_url = "https://ru.wikipedia.org/wiki/"
	parsed_data["links"] = [base_url + link["*"] for link in data["parse"]["links"] if link["ns"] == 0]

	return parsed_data


query = "Металлургия"
data = get_wikipedia_data(query)

# Сохранение результатов в JSON
with open("data.json", "w", encoding="utf-8") as file:
	json.dump(data, file, ensure_ascii=False, indent=4)

print(f"Data for '{query}' has been saved to 'data.json'")
