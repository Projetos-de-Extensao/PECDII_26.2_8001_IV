from django.db import migrations, models


def classificar_agendamentos_existentes(apps, schema_editor):
    Agendamento = apps.get_model("agendamentos", "Agendamento")
    Participacao = apps.get_model(
        "agendamentos",
        "ParticipacaoAgendamento",
    )

    for agendamento in Agendamento.objects.all().iterator():
        quantidade = Participacao.objects.filter(
            agendamento_id=agendamento.pk
        ).count()
        if quantidade > 1:
            agendamento.modalidade = "grupo"
            agendamento.limite_participantes = quantidade
            agendamento.save(update_fields=[
                "modalidade",
                "limite_participantes",
            ])


class Migration(migrations.Migration):

    dependencies = [
        ("agendamentos", "0003_campos_cancelamento"),
    ]

    operations = [
        migrations.AddField(
            model_name="agendamento",
            name="limite_participantes",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="agendamento",
            name="modalidade",
            field=models.CharField(
                choices=[
                    ("individual", "Individual"),
                    ("grupo", "Em grupo"),
                ],
                default="individual",
                max_length=12,
            ),
        ),
        migrations.RunPython(
            classificar_agendamentos_existentes,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="agendamento",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        ("limite_participantes", 1),
                        ("modalidade", "individual"),
                    )
                    | models.Q(
                        ("limite_participantes__gte", 2),
                        ("modalidade", "grupo"),
                    )
                ),
                name="agendamento_modalidade_limite_valido",
            ),
        ),
    ]
