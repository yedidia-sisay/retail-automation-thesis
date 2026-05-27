from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vision', '0002_alter_detectedobject_detection_run'),
    ]

    operations = [
        migrations.CreateModel(
            name='CameraConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('terminal_id', models.CharField(max_length=128)),
                ('camera_role', models.CharField(
                    choices=[('SKU', 'SKU Camera'), ('WEIGHTED', 'Weighted Camera')],
                    max_length=16,
                )),
                ('source_type', models.CharField(
                    choices=[('MOCK_FOLDER', 'Mock Folder'), ('USB', 'USB Camera'), ('NETWORK', 'Network / IP Camera')],
                    default='MOCK_FOLDER',
                    max_length=16,
                )),
                ('is_active', models.BooleanField(default=True)),
                ('mock_folder_path', models.CharField(blank=True, max_length=1024, null=True)),
                ('usb_device_index', models.IntegerField(blank=True, null=True)),
                ('stream_url', models.CharField(blank=True, max_length=2048, null=True)),
                ('frame_interval_ms', models.IntegerField(default=1000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ('terminal_id', 'camera_role'),
            },
        ),
        migrations.AddConstraint(
            model_name='cameraconfig',
            constraint=models.UniqueConstraint(
                fields=['terminal_id', 'camera_role'],
                name='unique_camera_config_per_terminal_role',
            ),
        ),
        migrations.AddIndex(
            model_name='cameraconfig',
            index=models.Index(fields=['terminal_id'], name='vision_came_termina_idx'),
        ),
        migrations.AddIndex(
            model_name='cameraconfig',
            index=models.Index(fields=['terminal_id', 'camera_role'], name='vision_came_termina_role_idx'),
        ),
    ]
