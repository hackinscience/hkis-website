from modeltranslation.translator import translator, TranslationOptions
from .models import Category, Exercise, Page


class ExerciseTranslationOptions(TranslationOptions):
    fields = ("title", "wording")


class CategoryTranslationOptions(TranslationOptions):
    fields = ("title",)


class PageTranslationOptions(TranslationOptions):
    fields = ("title", "body")


translator.register(Exercise, ExerciseTranslationOptions)
translator.register(Category, CategoryTranslationOptions)
translator.register(Page, PageTranslationOptions)
