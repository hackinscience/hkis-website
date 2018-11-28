from django.contrib import admin
from website.models import Answer, Exercise


class ExerciseAdmin(admin.ModelAdmin):
    readonly_fields = ("id",)
    list_display = ("position", "title")


class AnswerAdmin(admin.ModelAdmin):
    readonly_fields = ("user",)


admin.site.register(Answer, AnswerAdmin)
admin.site.register(Exercise, ExerciseAdmin)
