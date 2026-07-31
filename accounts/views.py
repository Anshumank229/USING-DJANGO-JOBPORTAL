from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Profile
from .serializers import ProfileSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Public endpoint — anyone can sign up as a candidate or recruiter.
    Rate-limited (see REST_FRAMEWORK.DEFAULT_THROTTLE_RATES['register'])
    since this is an unauthenticated, publicly reachable endpoint."""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'


class MeView(APIView):
    """GET the logged-in user's own account + profile in one call."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    """Retrieve/update the logged-in user's profile (bio, skills, avatar, etc.)."""
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile
