from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import Group
from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework import viewsets, response, serializers, routers, permissions
import django_filters

from website.models import Answer, Exercise, Snippet, User, Category, Page


class DjangoModelPermissionsStrict(permissions.DjangoModelPermissions):
    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": [],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


class ExercisePermission(permissions.DjangoModelPermissions):
    """Allow exercise author (and superusers) to modify them.

    Also anyone can create new (unpublished) exercises.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser or (
            request.user.is_authenticated and obj.author == request.user
        )


class AnswerPermission(permissions.BasePermission):
    """
    Object-level permission to only allow answers to be:
    - Created by anyone, but not modified.
    - Seen (read-only) by their owners only.
    - Staff is root and can see everything.
    """

    update_allows_field = ["is_shared"]

    def has_permission(self, request, view):
        """Authenticated users can create (POST) but not edit."""
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if request.method in ("POST", "DELETE"):
            # Logged in user can answer and update/delete their answer
            return True
        if request.method == "PATCH":
            # We authorized patch only if the field is authorized
            return all(key in self.update_allows_field for key in request.data.keys())
        if request.method in permissions.SAFE_METHODS:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        """Users can only see and modify own answers"""
        if request.user.is_superuser:
            return True
        if request.user.is_authenticated and obj.user == request.user:
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


class PageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Page
        fields = ("url", "slug", "title", "position")


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


class ExerciseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Exercise
        fields = "__all__"
        read_only_fields = ("is_published", "author")

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)
        super().__init__(*args, **kwargs)
        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [DjangoModelPermissionsStrict]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = [DjangoModelPermissionsStrict]
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.DjangoModelPermissions]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class PageViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.DjangoModelPermissions]
    queryset = Page.objects.all()
    serializer_class = PageSerializer


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
        if self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.user.is_superuser:
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
        if self.request.user.is_superuser:
            queryset = super().get_queryset()
            executed_at = self.request.query_params.get("executed_at__isnull", None)
            if executed_at is not None:
                queryset = queryset.filter(executed_at__isnull=True)
            return queryset
        return super().get_queryset().filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.user.is_superuser:
            return StaffSnippetSerializer
        return PublicSnippetSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExerciseViewSet(viewsets.ModelViewSet):
    permission_classes = [ExercisePermission]
    queryset = Exercise.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def list(self, request, *args, **kwargs):
        """Non-paginating copy of super().list, which calls get_serializer once per item."""
        queryset = list(self.filter_queryset(self.get_queryset()))
        return response.Response(
            {
                "count": len(queryset),
                "results": [self.get_serializer(item).data for item in queryset],
            }
        )

    def get_serializer(self, instance=None, *args, **kwargs):
        """I tweaked the `list` method so the get_serializer always receive an
        instance as first parameter (no many=True), so we can specialize serializer
        per instance. This is so exercises owner can see / edit their check.
        """
        kwargs["context"] = self.get_serializer_context()
        if self.action == "list":
            return ExerciseSerializer(
                instance,
                *args,
                **kwargs,
                fields=("url", "title", "wording", "is_published", "category")
            )
        return ExerciseSerializer(instance, *args, **kwargs)


router = routers.DefaultRouter()
router.register(r"answers", AnswerViewSet)
router.register(r"snippets", SnippetViewSet)
router.register(r"exercises", ExerciseViewSet)
router.register(r"groups", GroupViewSet)
router.register(r"users", UserViewSet)
router.register(r"categories", CategoryViewSet)
router.register(r"pages", PageViewSet)
