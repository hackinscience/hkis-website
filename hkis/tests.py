from django.contrib.auth.models import Permission, User, Group
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework.test import APITestCase
from hkis.models import UserInfo, Exercise, Page, Category, Answer


class TestRankUserWithInfo(TestCase):
    fixtures = ["initial"]

    def setUp(self):
        self.user = User.objects.create(username="Temporary")
        self.userinfo, _ = UserInfo.objects.get_or_create(user=self.user)
        self.client.force_login(self.user)

    def test_recompute_rank(self):
        self.userinfo.recompute_rank()
        assert User.objects.get(username="Temporary").hkis.rank == 2

    def test_recompute_ranks(self):
        UserInfo.objects.recompute_ranks()
        assert User.objects.get(username="Temporary").hkis.rank == 2


class TestRankUserWithNoInfo(TestCase):
    fixtures = ["initial"]

    def setUp(self):
        self.user = User.objects.create(username="Temporary")

    def test_recompute_ranks(self):
        UserInfo.objects.recompute_ranks()


class TestGetPublicTeams(TestCase):
    fixtures = ["initial"]

    def test_public_teams(self):
        assert User.objects.get(username="mdk").hkis.public_teams()


class TestPages(TestCase):
    fixtures = ["initial"]

    def test_page(self):
        p1 = Page.objects.first()
        assert p1.slug in p1.get_absolute_url()


class TestCategories(TestCase):
    fixtures = ["initial"]

    def test_unnamed_category(self):
        c1 = Category.objects.create()
        assert str(c1) == "Unnamed"

    def test_named_category(self):
        assert str(Category.objects.first()) != "Unnamed"


class TestAdminSuperUser(TestCase):
    fixtures = ["initial"]

    def setUp(self):
        self.client.force_login(User.objects.get(username="mdk"))

    def test_get_admin_exercises(self):
        response = self.client.get("/admin/hkis/exercise/")
        assert b"Hello World" in response.content

    def test_get_admin_exercises_1(self):
        response = self.client.get("/admin/hkis/exercise/1/change/")
        assert b"Hello World" in response.content


# class TestStaffCanCreateExercise(LiveServerTestCase):
#     fixtures = ["initial"]
#
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.selenium = WebDriver()
#         cls.selenium.implicitly_wait(10)
#
#     @classmethod
#     def tearDownClass(cls):
#         cls.selenium.quit()
#         super().tearDownClass()
#
#     def test_login(self):
#         self.selenium.get("%s%s" % (self.live_server_url, "/accounts/login/"))
#         username_input = self.selenium.find_element_by_name("username")
#         username_input.send_keys("Lisa")
#         password_input = self.selenium.find_element_by_name("password")
#         password_input.send_keys("boisminrosael")
#         self.selenium.find_element_by_xpath('//button[text()="Sign in"]').click()
#         self.selenium.get(self.live_server_url + "/admin/hkis/exercise/add/")
#         title_input = self.selenium.find_element_by_id("id_title_en")
#         title_input.send_keys = "Lisa's Exercise"
#         page_select = Select(self.selenium.find_element_by_id("id_page"))
#         page_select.select_by_index(1)
#         self.selenium.find_element_by_xpath('//input[@value="Save"]').click()


def set_teacher_permissions():
    teacher = Group.objects.get(name="Teacher")
    exercise_content_type = ContentType.objects.get_for_model(Exercise)
    answer_content_type = ContentType.objects.get_for_model(Answer)
    for content_type, perm in (
        (answer_content_type, "view_answer"),
        (answer_content_type, "change_answer"),
        (exercise_content_type, "add_exercise"),
        (exercise_content_type, "change_exercise"),
        (exercise_content_type, "view_exercise"),
        (exercise_content_type, "delete_exercise"),
    ):
        permission = Permission.objects.get(codename=perm)
        teacher.permissions.add(permission)


class TestAdminStaffWithTeacherGroup(TestCase):
    fixtures = ["initial"]

    def setUp(self):
        self.user = User.objects.get(username="Lisa")
        set_teacher_permissions()
        self.client.force_login(self.user)

    def test_get_admin_exercises(self):
        response = self.client.get("/admin/hkis/exercise/")
        assert b"Hello World" not in response.content  # mdk's exercise
        assert b"Print 42" in response.content  # Lisa's exercise

    def test_get_admin_exercises_1(self):
        """Exercise 1 is owned by mdk, Lisa can't view it."""
        response = self.client.get("/admin/hkis/exercise/1/change/")
        assert response.status_code == 302

    def test_get_admin_exercises_2(self):
        """Exercise 1 is owned by Lisa, Lisa can view it."""
        response = self.client.get("/admin/hkis/exercise/2/change/")
        assert response.status_code == 200

    def test_create_exercise(self):
        response = self.client.post(
            "/admin/hkis/exercise/add/",
            {"title_en": "Lisa's exercise", "page": 1, "position": 100, "points": 1},
        )
        assert response.status_code == 302
        created = Exercise.objects.get(title="Lisa's exercise")
        assert created.is_published is False  # A staff can't self-publish exercises
        assert created.author == self.user
        assert created.category.title == "Sandbox"  # All new exercises to the sandbox


class TestAPIAnswerAnonymous(APITestCase):
    fixtures = ["initial"]

    def test_get_answer(self):
        response = self.client.get("/api/answers/")
        assert response.status_code == 403


class TestAPIAnswerAuthed(APITestCase):
    fixtures = ["initial"]

    def setUp(self):
        user = User.objects.get(username="mdk")
        self.client.force_authenticate(user=user)

    def test_get_answer(self):
        response = self.client.get("/api/answers/")
        assert response.status_code == 200
        assert response.json()["results"]
