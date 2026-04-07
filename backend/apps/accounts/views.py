from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAdmin, IsSelfOrAdmin
from .serializers import (
    ChangePasswordSerializer,
    UserCreateSerializer,
    UserProfileSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from .models import UserProfile

User = get_user_model()


class LoginView(APIView):
    """Custom login: returns tokens + user data."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "")
        password = request.data.get("password", "")

        # USERNAME_FIELD is email, so pass email as username to authenticate
        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response(
                {"detail": "Неверный email или пароль"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "Аккаунт деактивирован"},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            "user": UserSerializer(user).data,
        })


class RegisterView(APIView):
    """Registration: creates user and returns tokens + user data."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            "user": UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """Blacklist refresh token on logout."""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            refresh = request.data.get("refresh")
            if refresh:
                token = RefreshToken(refresh)
                token.blacklist()
        except Exception:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related("profile").all()
    filterset_fields = ["role", "is_active", "language"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering_fields = ["date_joined", "last_login", "email"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        if self.action in ("list", "destroy"):
            return [IsAdmin()]
        if self.action in ("update", "partial_update", "retrieve"):
            return [IsSelfOrAdmin()]
        return [IsAuthenticated()]

    @action(detail=False, methods=["get", "patch"], permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        if request.method == "PATCH":
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(UserSerializer(user).data)
        return Response(UserSerializer(user).data)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get", "patch"], permission_classes=[IsAuthenticated])
    def profile(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if request.method == "PATCH":
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(UserProfileSerializer(profile).data)
