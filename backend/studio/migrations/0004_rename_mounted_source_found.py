from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("studio", "0003_inferenceserver_alter_job_kind")]

    operations = [migrations.RenameField(model_name="source", old_name="mounted", new_name="found")]
