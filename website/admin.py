from django.contrib import admin
from website.models import Answer, Exercise

class ExerciseAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'title', )

admin.site.register(Answer)
admin.site.register(Exercise, ExerciseAdmin)
