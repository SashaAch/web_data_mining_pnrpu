from steam import Steam
import requests
from bs4 import BeautifulSoup
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import OneHotEncoder
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()
# Ваш ключ API Steam
KEY = os.getenv('STEAM_API_KEY')
# Список игр
games = [
    "Bioshock Infinite", "DayZ", "Portal 2", "Counter Strike 2",
    "Apex Legends", "Dota 2", "PAYDAY 2", "Control Ultimate Edition", "Cyberpunk 2077",
    "Left 4 Dead 2"
]


class GameRecommender:
    def __init__(self, steam_api_key, games):
        self.steam = Steam(steam_api_key)
        self.games = games
        self.game_genres = {}
        self.similar_games = {}
        self.game_to_id = {}
        self.id_to_game = {}
        self.encoder = OneHotEncoder()
        self.knn = NearestNeighbors(n_neighbors=5, metric='cosine')

    def get_game_id(self, game_name):
        response = self.steam.apps.search_games(game_name)
        if response and 'apps' in response and len(response['apps']) > 0:
            return response['apps'][0].get('id')
        return None

    def get_game_genres(self, game_id):
        try:
            details = self.steam.apps.get_app_details(game_id, filters='genres')
            if str(game_id) in details and 'data' in details[str(game_id)]:
                return [genre['description'] for genre in details[str(game_id)]['data']['genres']]
        except Exception as ex:
            print(ex)
        return []

    def search_games_by_genre(self, genre, exclude_games):
        search_url = f"https://store.steampowered.com/search/?term={genre}"
        response = requests.get(search_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        games_list = []
        for game in soup.find_all('a', class_='search_result_row', limit=20):
            game_name = game.find('span', class_='title').text
            if game_name not in exclude_games and len(games_list) < 10:
                game_data = {'name': game_name, 'link': game['href']}
                games_list.append(game_data)
        return games_list

    def process_games(self):
        for game in self.games:
            game_id = self.get_game_id(game)
            if game_id:
                genres = self.get_game_genres(game_id)
                self.game_genres[game] = genres

    def find_similar_games(self):
        self.all_game_genres = {game: genres for game, genres in self.game_genres.items()}  # Копируем оригинальные жанры
        for game, genres in self.game_genres.items():
            for genre in genres:
                for similar_game in self.search_games_by_genre(genre, self.games):
                    if similar_game['name'] not in self.all_game_genres:
                        similar_game_id = self.get_game_id(similar_game['name'])
                        if similar_game_id:
                            similar_game_genres = self.get_game_genres(similar_game_id)
                            self.all_game_genres[similar_game['name']] = similar_game_genres

    def create_game_matrix(self):
        # Список уникальных игр и жанров
        unique_games = set(self.all_game_genres.keys())
        unique_genres = set(genre for genres in self.all_game_genres.values() for genre in genres)

        # Сопоставление игр и жанров с индексами
        self.game_to_id = {game: idx for idx, game in enumerate(unique_games)}
        self.id_to_game = {idx: game for game, idx in self.game_to_id.items()}
        self.genre_to_id = {genre: idx for idx, genre in enumerate(unique_genres)}

        # Создание матрицы
        game_matrix = np.zeros((len(self.game_to_id), len(self.genre_to_id)))
        for game, genres in self.all_game_genres.items():
            game_idx = self.game_to_id[game]
            for genre in genres:
                genre_idx = self.genre_to_id[genre]
                game_matrix[game_idx, genre_idx] = 1

        self.knn.fit(game_matrix)
        return game_matrix

    def get_recommendations(self, game_name, game_matrix):
        if game_name in self.game_to_id:
            game_idx = self.game_to_id[game_name]
            distances, indices = self.knn.kneighbors([game_matrix[game_idx]])
            recommendations = [self.id_to_game[idx] for idx in indices[0] if self.id_to_game[
                idx] not in self.games and idx != game_idx]  # Исключаем исходную игру и все игры из первоначального списка
            return recommendations
        return []


# Пример использования
recommender = GameRecommender(KEY, games)
recommender.process_games()
recommender.find_similar_games()
game_matrix = recommender.create_game_matrix()
recommendations = {game: recommender.get_recommendations(game, game_matrix) for game in games}
print(recommendations)

