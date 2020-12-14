import django_filters

from asgiref.sync import async_to_sync
from django.contrib.auth.models import Group
from django_filters import rest_framework as filters
from channels.layers import get_channel_layer
from rest_framework import permissions
from rest_framework import routers
from rest_framework import serializers
from rest_framework import viewsets
from website.models import Answer, Exercise, Snippet, User, Category


class AdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_staff:
            return True
        return request.method in permissions.SAFE_METHODS


class AnswerPermission(permissions.BasePermission):
    """
    Object-level permission to only allow answers to be:
    - Created by anyone, but not modified.
    - Seen (read-only) by their owners only.
    - Staff is root and can see everything.
    """

    def has_permission(self, request, view):
        """Authenticated users can create (POST) but not edit."""
        if not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        if request.user.is_authenticated:
            UPDATE_ALLOWS_FIELD = ["is_shared"]
            if request.method == "POST":
                # Logged in user can answer and update their answer
                return True
            elif request.method == "PATCH":
                # We authorized patch only if the field is authorized
                for key in request.data.keys():
                    if key not in UPDATE_ALLOWS_FIELD:
                        return False
                return True
        if request.method in permissions.SAFE_METHODS:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        """Users can only see and modify own answers"""
        if request.user.is_staff:
            return True
        elif request.user.is_authenticated and obj.user == request.user:
            return True
        return False


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ("url", "username", "first_name", "last_name", "email", "groups")


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ("url", "name")


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = ("slug", "title", "position")


class StaffAnswerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"


class PublicAnswerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"
        read_only_fields = (
            "user",
            "is_corrected",
            "is_valid",
            "correction_message",
            "created_at",
            "corrected_at",
        )


class StaffSnippetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Snippet
        fields = "__all__"


class PublicSnippetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Snippet
        fields = "__all__"
        read_only_fields = ("user", "created_at", "executed_at", "output")


class StaffExerciseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Exercise
        fields = "__all__"


class PublicExerciseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Exercise
        fields = ("url", "title", "wording")


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminOrReadOnly]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class AnswerFilter(filters.FilterSet):
    username = django_filters.CharFilter(field_name="user__username")

    class Meta:
        model = Answer
        fields = ("is_corrected", "is_valid", "user")


class AnswerViewSet(viewsets.ModelViewSet):
    permission_classes = [AnswerPermission]
    queryset = Answer.objects.all()
    filterset_class = AnswerFilter

    def cb_new_answer(self, instance):
        group = "answers.{}.{}".format(instance.user.id, instance.exercise.id)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group,
            {
                "type": "correction",
                "exercise": instance.exercise.id,
                "correction_message": instance.correction_message,
                "answer": instance.id,
                "is_corrected": instance.is_corrected,
                "is_valid": instance.is_valid,
            },
        )

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return StaffAnswerSerializer
        return PublicAnswerSerializer

    def perform_update(self, serializer):
        instance = serializer.save()
        if "is_corrected" in serializer.validated_data:
            self.cb_new_answer(instance)

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        self.cb_new_answer(instance)


class SnippetViewSet(viewsets.ModelViewSet):
    permission_classes = [AnswerPermission]  # Snippets are like answers: Create only.
    queryset = Snippet.objects.all()
    filterset_fields = ("executed_at",)

    def get_queryset(self):
        if self.request.user.is_staff:
            queryset = super().get_queryset()
            executed_at = self.request.query_params.get("executed_at__isnull", None)
            if executed_at is not None:
                queryset = queryset.filter(executed_at__isnull=True)
            return queryset
        return super().get_queryset().filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return StaffSnippetSerializer
        return PublicSnippetSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExerciseViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminOrReadOnly]
    queryset = Exercise.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(is_published=True)

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return StaffExerciseSerializer
        return PublicExerciseSerializer


router = routers.DefaultRouter()
router.register(r"answers", AnswerViewSet)
router.register(r"snippets", SnippetViewSet)
router.register(r"exercises", ExerciseViewSet)
router.register(r"groups", GroupViewSet)
router.register(r"users", UserViewSet)
router.register(r"categories", CategoryViewSet)
