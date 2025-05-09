# Generated by Django 5.0.2 on 2024-03-08 14:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("video_processor", "0034_alter_image_url_alter_video_web_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="thumbnail",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="videoThumbnail",
                to="video_processor.image",
            ),
        ),
    ]
