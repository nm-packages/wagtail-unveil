from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="sort_order",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
