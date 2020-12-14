from modeltranslation.translator import translator, TranslationOptions
from .models import Category, Exercise


class ExerciseTranslationOptions(TranslationOptions):
    fields = ("title", "wording")


class CategoryTranslationOptions(TranslationOptions):
    fields = ("title",)


translator.register(Exercise, ExerciseTranslationOptions)
translator.register(Category, CategoryTranslationOptions)
