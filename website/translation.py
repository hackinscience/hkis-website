from modeltranslation.translator import translator, TranslationOptions
from .models import Exercise


class ExerciseTranslationOptions(TranslationOptions):
    fields = ("title", "wording")


translator.register(Exercise, ExerciseTranslationOptions)
