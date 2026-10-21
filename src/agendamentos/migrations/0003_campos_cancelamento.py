from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agendamentos", "0002_participacao_agendamento"),
    ]

    operations = [
        migrations.AddField(
            model_name="agendamento",
            name="cancelado_em",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="agendamento",
            name="motivo_cancelamento",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="participacaoagendamento",
            name="cancelado_em",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="participacaoagendamento",
            name="motivo_cancelamento",
            field=models.TextField(blank=True),
        ),
    ]
