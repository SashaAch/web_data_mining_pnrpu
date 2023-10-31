import requests
from bs4 import BeautifulSoup
import zipfile


def download_images_from_url(url, zip_name="downloaded_images.zip"):
	try:
		response = requests.get(url)
		response.raise_for_status()

		# Инициализация BeautifulSoup
		soup = BeautifulSoup(response.text, 'html.parser')

		# Поиск всех изображений
		img_tags = soup.find_all('img')
		source_tags = soup.find_all('source')

		# Список URL-адресов всех изображений
		img_urls = [img['src'] for img in img_tags if 'src' in img.attrs]

		# Добавляем изображения из source тегов (если есть)
		for source in source_tags:
			if 'srcset' in source.attrs:
				srcset = source['srcset'].split(',')
				img_urls.extend([src.strip().split()[0] for src in srcset])

		# Создание ZIP-архива
		with zipfile.ZipFile(zip_name, 'w') as zipf:
			for i, img_url in enumerate(img_urls):
				img_response = requests.get(img_url)
				img_name = f"image_{i + 1}.jpg"
				zipf.writestr(img_name, img_response.content)
				print(f"Downloaded {img_url} as {img_name}")

		print(f"All images downloaded and saved as {zip_name}")

	except Exception as e:
		print(f"An error occurred: {e}")



url = 'https://drom.ru'
download_images_from_url(url)
