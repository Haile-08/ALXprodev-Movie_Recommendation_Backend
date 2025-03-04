from drf_yasg import openapi
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from .views import TrendingMoviesView, MovieRecommendationView, UserLoginView, UserSignupView, FavoriteMovieView

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

urlpatterns = [
    path('signup/', UserSignupView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('trending/', TrendingMoviesView.as_view(), name='trending-movies'),
    path('recommend/<int:movie_id>/', MovieRecommendationView.as_view(), name='movie-recommendations'),
    path('favorites/', FavoriteMovieView.as_view(), name='favorite-movies'),
    path('docs', schema_view.with_ui('swagger', cache_timeout=0),
         name='swagger-ui'),
]