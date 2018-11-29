from django.contrib.auth.models import User, Group
from rest_framework import permissions
from rest_framework import routers
from rest_framework import serializers
from rest_framework import viewsets
from website.models import Answer, Exercise, Snippet


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
        """Authenticated users can create (POST) but not edit.
        """
        if request.user.is_staff:
            return True
        if request.method == "POST" and request.user.is_authenticated:
            # Logged in user can answer.
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        """Users can only see their own answers, can't even modify them.
        """
        if request.user.is_staff:
            return True
        return obj.user == request.user and request.method in permissions.SAFE_METHODS


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ("url", "username", "first_name", "last_name", "email", "groups")


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ("url", "name")


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
        model = Answer
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


class AnswerViewSet(viewsets.ModelViewSet):
    permission_classes = [AnswerPermission]
    queryset = Answer.objects.all()
    filter_fields = ("is_corrected",)

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return StaffAnswerSerializer
        return PublicAnswerSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SnippetViewSet(viewsets.ModelViewSet):
    permission_classes = [AnswerPermission]  # Snippets are like answers: Create only.
    queryset = Snippet.objects.all()
    filter_fields = ("executed_at",)

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
