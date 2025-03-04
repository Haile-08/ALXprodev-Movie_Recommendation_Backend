import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response

class TrendingMoviesView(APIView):
    def get(self, request):
        url = "https://api.themoviedb.org/3/trending/movie/day?language=en-US"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {settings.TMDB_API_KEY}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return Response(data)
        return Response({"error": "Failed to fetch movies"}, status=500)

class MovieRecommendationView(APIView):
    def get(self, request, movie_id):
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations?language=en-US&page=1"

        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {settings.TMDB_API_KEY}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return Response(response.json())
        return Response({"error": "Failed to fetch recommendations"}, status=500)
