import django.db.models.deletion
from django.db import migrations, models


def copiar_participacoes_existentes(apps, schema_editor):
    Agendamento = apps.get_model("agendamentos", "Agendamento")
    Participacao = apps.get_model(
        "agendamentos",
        "ParticipacaoAgendamento",
    )
    VinculoAntigo = Agendamento.atletas.through

    Participacao.objects.bulk_create(
        Participacao(
            agendamento_id=vinculo.agendamento_id,
            atleta_id=vinculo.atleta_id,
        )
        for vinculo in VinculoAntigo.objects.all().iterator()
    )


def restaurar_vinculos_antigos(apps, schema_editor):
    Agendamento = apps.get_model("agendamentos", "Agendamento")
    Participacao = apps.get_model(
        "agendamentos",
        "ParticipacaoAgendamento",
    )
    VinculoAntigo = Agendamento.atletas.through

    VinculoAntigo.objects.bulk_create(
        VinculoAntigo(
            agendamento_id=participacao.agendamento_id,
            atleta_id=participacao.atleta_id,
        )
        for participacao in Participacao.objects.all().iterator()
    )


class Migration(migrations.Migration):

    dependencies = [
        ("agendamentos", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ParticipacaoAgendamento",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "situacao",
                    models.CharField(
                        choices=[
                            ("confirmada", "Confirmada"),
                            ("cancelada", "Cancelada"),
                            ("presente", "Presente"),
                            ("falta", "Falta"),
                            ("falta_justificada", "Falta justificada"),
                        ],
                        default="confirmada",
                        max_length=20,
                    ),
                ),
                ("observacoes", models.TextField(blank=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                (
                    "agendamento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="participacoes",
                        to="agendamentos.agendamento",
                    ),
                ),
                (
                    "atleta",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="participacoes_agendamento",
                        to="usuarios.atleta",
                    ),
                ),
            ],
            options={
                "ordering": ("agendamento", "atleta"),
                "indexes": [
                    models.Index(
                        fields=["atleta", "situacao"],
                        name="agendamento_atleta__6136ab_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("agendamento", "atleta"),
                        name="participacao_unica_por_agendamento_atleta",
                    ),
                ],
            },
        ),
        migrations.RunPython(
            copiar_participacoes_existentes,
            restaurar_vinculos_antigos,
        ),
        migrations.RemoveField(
            model_name="agendamento",
            name="atletas",
        ),
        migrations.AddField(
            model_name="agendamento",
            name="atletas",
            field=models.ManyToManyField(
                related_name="agendamentos",
                through="agendamentos.ParticipacaoAgendamento",
                through_fields=("agendamento", "atleta"),
                to="usuarios.atleta",
            ),
        ),
    ]
