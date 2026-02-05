from authentication.models import UserProfile
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = UserProfile.objects.create_user(**validated_data)
        return user 


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Allow login using email or username.
    If an email is provided in `username`, map it to the actual username.
    """

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            # If user passed an email in the username field, map it to username
            if "@" in username:
                try:
                    user = UserProfile.objects.get(email=username)
                    attrs["username"] = user.username
                except UserProfile.DoesNotExist:
                    pass

        return super().validate(attrs)

    