# package import
import redis
import requests
from drf_yasg import openapi
from rest_framework import status
from rest_framework.views import APIView
from django.db.utils import IntegrityError
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
# Local import
from django.conf import settings
from .models import User, Favorite
from .serializers import FavoriteSerializer


redis_client = redis.StrictRedis.from_url(
    settings.CACHES["default"]["LOCATION"],
    decode_responses=True
    )
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {settings.TMDB_API_KEY}"
}


class UserSignupView(APIView):
    # swagger signup schema to input user info
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                "email",
                "first_name",
                "last_name",
                "password"
            ],
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="email",
                    description="User's email"
                    ),
                "first_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="User's first name"
                    ),
                "last_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="User's last name"
                    ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="password",
                    description="User's password"
                    ),
            },
        ),
        responses={
            201: openapi.Response("User created successfully"),
            400: openapi.Response("Bad request - validation error"),
            500: openapi.Response("Internal server error"),
        },
    )

    def post(self, request):
        """
        Signup new user
        """
        try:
            email = request.data.get("email")
            first_name = request.data.get("first_name")
            last_name = request.data.get("last_name")
            password = request.data.get("password")

            if not email or not first_name or not last_name or not password:
                # check if all the fields are specified
                return Response(
                    {"error": "All fields are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if User.objects.filter(email=email).exists():
                # check if the user already exists
                return Response(
                    {"error": "Email already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            return Response(
                {"message": "User created successfully"},
                status=status.HTTP_201_CREATED
            )

        except IntegrityError:
            return Response(
                {"error": "Database integrity error"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Something went wrong", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserLoginView(APIView):
    # swagger signup schema to input user info
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="email",
                    description="User's email"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="password",
                    description="User's password"
                ),
            },
        ),
        responses={
            201: openapi.Response("User created successfully"),
            400: openapi.Response("Bad request - validation error"),
            500: openapi.Response("Internal server error"),
        },
    )

    def post(self, request):
        """
        login user
        """
        try:
            email = request.data.get("email")
            password = request.data.get("password")

            if not email or not password:
                # check if password and email fields are specified
                return Response(
                    {"error": "Email and password are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = User.objects.filter(email=email).first()
            # auth user with password
            if user and user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }, status=status.HTTP_200_OK)

            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        except Exception as e:
            return Response(
                {"error": "Something went wrong", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrendingMoviesView(APIView):
    def get(self, request):
        try:
            cache_key = "trending_movies"
            cached_data = redis_client.get(cache_key)

            if cached_data:
                # check if there is cached data
                return Response(eval(cached_data))

            url = "https://api.themoviedb.org/3/trending/movie/day?language=en-US"

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                # check if the response is okay
                data = response.json()
                #  Cache for 1 hour
                redis_client.setex(cache_key, 3600, str(data))
                return Response(data, status=status.HTTP_200_OK)

            return Response(
                {"error": f"Failed to fetch movies: {response.status_code}"},
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {"error": "External API request failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MovieRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer Token for authentication",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: "Success - Returns movie recommendations",
            400: "Bad Request - Invalid movie ID",
            401: "Unauthorized - Provide a valid token",
            500: "Server Error - External API failure",
        }
    )
    def get(self, request, movie_id):
        try:
            url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations?language=en-US&page=1"

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                # check if the response is okay
                return Response(response.json(), status=status.HTTP_200_OK)

            return Response(
                {
                    "error": f"Failed to fetch recommendations: {response.status_code}"
                },
                status=response.status_code
            )

        except requests.exceptions.RequestException as e:
            return Response(
                {"error": "External API request failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FavoriteMovieView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["movie_id", "title", "overview", "password"],
            properties={
                "movie_id": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Movie id"
                ),
                "title": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Movie title"
                ),
                "overview": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Movie overview"
                ),
                "poster": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Movie poster URL"
                ),
                "language": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Movie language"
                ),
                "rating": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    format="float",
                    description="Movie rating"
                ),
            },
        ),
        responses={
            201: openapi.Response("Movie saved as favorite."),
            400: openapi.Response("Bad request - validation error"),
            500: openapi.Response("Internal server error"),
        },
    )
    def post(self, request):
        try:
            serializer = FavoriteSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(
                    {"message": "Movie saved as favorite"},
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": "Something went wrong", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer Token for authentication",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: "Success - Returns movie recommendations",
            400: "Bad Request - Invalid movie ID",
            401: "Unauthorized - Provide a valid token",
            500: "Server Error - External API failure",
        }
    )

    def get(self, request):
        try:
            favorites = Favorite.objects.filter(user=request.user)
            serializer = FavoriteSerializer(favorites, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {
                    "error": "Failed to fetch favorite movies",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
