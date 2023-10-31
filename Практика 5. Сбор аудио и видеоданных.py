import os
import requests
import youtube_dl



def download_reddit_videos(subreddit, output_folder, max_downloads=10):
	base_url = f'https://www.reddit.com/r/{subreddit}/hot.json'
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
	}

	ydl_opts = {
		'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
	}

	response = requests.get(base_url, headers=headers)
	data = response.json()

	if not os.path.exists(output_folder):
		os.makedirs(output_folder)

	download_count = 0
	for post in data['data']['children']:
		if 'secure_media' in post['data'] and post['data']['secure_media'] is not None:
			if 'reddit_video' in post['data']['secure_media']:
				video_url = post['data']['secure_media']['reddit_video']['fallback_url']

				if download_count >= max_downloads:
					break

				with youtube_dl.YoutubeDL(ydl_opts) as ydl:
					ydl.download([video_url])

				download_count += 1


# Пример использования:
download_reddit_videos('videomemes', './reddit_videos', 10)
