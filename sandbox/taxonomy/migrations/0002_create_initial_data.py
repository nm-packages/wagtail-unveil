from django.db import migrations


def create_initial_data(apps, schema_editor):
    Category = apps.get_model("taxonomy", "Category")
    Colour = apps.get_model("taxonomy", "Colour")

    for name in ["News", "Events", "Blog"]:
        Category.objects.create(name=name)

    for name in ["Red", "Green", "Blue"]:
        Colour.objects.create(name=name)


def remove_initial_data(apps, schema_editor):
    Category = apps.get_model("taxonomy", "Category")
    Colour = apps.get_model("taxonomy", "Colour")

    Category.objects.filter(name__in=["News", "Events", "Blog"]).delete()
    Colour.objects.filter(name__in=["Red", "Green", "Blue"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("taxonomy", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_initial_data, remove_initial_data),
    ]
