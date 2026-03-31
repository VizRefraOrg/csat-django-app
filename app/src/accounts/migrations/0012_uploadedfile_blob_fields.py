from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_remove_account_membership_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadedfile',
            name='blob_name',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='uploadedfile',
            name='blob_url',
            field=models.URLField(blank=True, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='uploadedfile',
            name='blob_size',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='uploadedfile',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='accounts.models.user_directory_path'),
        ),
    ]
