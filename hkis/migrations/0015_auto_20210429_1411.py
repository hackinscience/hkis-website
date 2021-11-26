# Generated by Django 3.1.6 on 2021-04-29 12:11

from django.db import migrations


def create_exercise_page(apps, schema_editor):
    Page = apps.get_model("hkis", "Page")
    Exercise = apps.get_model("hkis", "Exercise")
    try:
        exercises_page = Page.objects.get(url="exercises")
    except Page.DoesNotExist:
        exercises_page = Page.objects.create(
            url="exercises",
            title="Exercises",
            title_en="Exercises",
            title_fr="Exercices",
            body="empty",
            body_en="Add exercises using [/admin/](/admin/) and edit this message.",
            body_fr="Ajoutez des exercices via [/admin/](/admin/) et éditez ce message.",
            in_menu=True,
        )


def create_help_page(apps, schema_editor):
    Page = apps.get_model("hkis", "Page")
    if Page.objects.filter(url="help").exists():
        return
    body = """# Getting help

## Report a bug on hackinscience

If you found an issue in the hkis, please fill a bug [in our
bugtracker](https://framagit.org/hackinscience/hkis-hkis/issues).
"""

    Page.objects.create(
        url="help",
        title="Help",
        title_en="Help",
        title_fr="Aide",
        body=body,
        body_en=body,
        body_fr="""# Obtenir de l'aide

## Signaler un bug trouvé sur HackInScience

Si vous avez trouvé un bug sur le site vous pouvez ouvrir [un
ticket](https://framagit.org/hackinscience/hkis-hkis/ issues).
""",
        position=1,
        in_menu=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("hkis", "0014_auto_20210411_2136"),
    ]

    operations = [
        migrations.RunPython(create_exercise_page),
        migrations.RunPython(create_help_page),
    ]
