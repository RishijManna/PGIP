import django.core.validators
import my_app.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("my_app", "0036_exam_application_fee_exam_application_url_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="file",
            field=models.FileField(
                upload_to=my_app.models.document_upload_path,
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["pdf", "jpg", "jpeg", "png", "doc", "docx"]
                    ),
                    my_app.models.validate_document_file,
                ],
            ),
        ),
    ]
