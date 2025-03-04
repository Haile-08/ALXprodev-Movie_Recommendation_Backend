from drf_yasg import openapi
from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from .views import (
    TrendingMoviesView,
    MovieRecommendationView,
    UserLoginView,
    UserSignupView,
    FavoriteMovieView
)

# create the schema for swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Movie Recommendation App API",
        default_version='v1',
        description="API documentation for the Travel App project",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@travelapp.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)
"""
The app route

signup: register new user
login: login user to get refresh and access token
trending: get all trending movies
recommend: get movie recommendations based on a movie selected
favorites: create and retrieve favorite movies

"""
urlpatterns = [
    path('users/signup/', UserSignupView.as_view(), name='signup'),
    path('users/login/', UserLoginView.as_view(), name='login'),
    path('movies/trending/', TrendingMoviesView.as_view(), name='trending-movies'),
    path('movies/recommend/<int:movie_id>/', MovieRecommendationView.as_view(),
         name='movie-recommendations'),
    path('favorites/', FavoriteMovieView.as_view(), name='favorite-movies'),
    path('docs', schema_view.with_ui('swagger', cache_timeout=0),
         name='swagger-ui'),
]
