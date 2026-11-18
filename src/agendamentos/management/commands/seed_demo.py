from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from agendamentos.models import Agendamento, Equipamento, Espaco
from agendamentos.services import criar_agendamento
from usuarios.models import (
    Atleta,
    DisponibilidadeProfissional,
    Funcionario,
    Profissional,
    Responsavel,
    Usuario,
)

SENHA = "demo1234"


def proximo_dia_util(a_partir_de, minimo=1):
    """Primeiro dia de segunda a sexta, pelo menos `minimo` dias à frente."""
    dia = a_partir_de + timedelta(days=minimo)
    while dia.weekday() > 4:
        dia += timedelta(days=1)
    return dia


def momento(dia, hora, minuto=0):
    return timezone.make_aware(datetime.combine(dia, time(hora, minuto)))


class Command(BaseCommand):
    help = "Cria dados FICTÍCIOS para demonstrar o sistema (pode rodar várias vezes)."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        def conta(username, nome, sobrenome):
            user, criado = User.objects.get_or_create(
                username=username,
                defaults={"first_name": nome, "last_name": sobrenome},
            )
            if criado:
                user.set_password(SENHA)
                user.is_staff = username == "recepcao"  # as telas exigem staff
                user.save()
            perfil, _ = Usuario.objects.get_or_create(
                user=user, defaults={"telefone": "(61) 99999-0000"}
            )
            return perfil

        # Equipe
        recep, _ = Funcionario.objects.get_or_create(
            usuario=conta("recepcao", "Rita", "Recepção"),
            defaults={"cargo": "Recepcionista"},
        )
        profissionais = []
        for username, nome, sobrenome, esp in (
            ("prof_ana", "Ana", "Souza", "Fisioterapia"),
            ("prof_bruno", "Bruno", "Lima", "Treinamento funcional"),
        ):
            prof, criado = Profissional.objects.get_or_create(
                usuario=conta(username, nome, sobrenome),
                defaults={"especialidade": esp},
            )
            if criado:
                for dia in range(0, 5):
                    for ini, fim in ((time(8, 0), time(12, 0)),
                                     (time(14, 0), time(18, 0))):
                        DisponibilidadeProfissional.objects.create(
                            profissional=prof, dia_semana=dia,
                            hora_inicio=ini, hora_fim=fim,
                        )
            profissionais.append(prof)
        ana, bruno = profissionais

        # Espaços e equipamentos
        sala, _ = Espaco.objects.get_or_create(
            nome="Sala 1", defaults={"tipo": "Sala", "capacidade": 2})
        quadra, _ = Espaco.objects.get_or_create(
            nome="Quadra coberta", defaults={"tipo": "Quadra", "capacidade": 8})
        bola, _ = Equipamento.objects.get_or_create(
            nome="Bola de vôlei", defaults={"tipo": "Bola"})
        Equipamento.objects.get_or_create(
            nome="Colchonete", defaults={"tipo": "Acessório"})

        # Atletas
        resp_user = conta("resp_marta", "Marta", "Ferreira")
        responsavel, _ = Responsavel.objects.get_or_create(
            usuario=resp_user, defaults={"telefone": "(61) 98888-1111"})

        def atleta(nome, nasc, **extra):
            return Atleta.objects.get_or_create(
                nome=nome, defaults={"data_de_nascimento": nasc, **extra})[0]

        joao = atleta("João Pereira", date(1998, 5, 10),
                      email="joao@exemplo.com", telefone="(61) 97777-2222",
                      objetivos="Ganho de condicionamento")
        carla = atleta("Carla Mendes", date(1992, 3, 22),
                       email="carla@exemplo.com", telefone="(61) 96666-3333")
        pedro = atleta("Pedro Ferreira (menor)", date(2012, 8, 3),
                       responsavel=responsavel)
        if pedro.usuario_id is None:
            pedro.usuario = conta("demo_pedro", "Pedro", "Ferreira")
            pedro.save(update_fields=["usuario"])

        luiza = atleta("Luiza Ribeiro", date(2000, 3, 12),
                       email="demo_luiza@example.com", telefone="21999990000")
        if luiza.usuario_id is None:
            luiza.usuario = conta("demo_luiza", "Luiza", "Ribeiro")
            luiza.save(update_fields=["usuario"])

        atleta("Lucas Prado (sem nascimento)", None)  # exemplo de cadastro incompleto
        visitante = atleta("Visitante Experimental", date(2000, 1, 15),
                           email="visitante@exemplo.com",
                           telefone="(61) 95555-4444")

        # Agendamentos de exemplo (só se ainda não existe nenhum)
        if Agendamento.objects.exists():
            self.stdout.write("Já existem agendamentos; não criei novos.")
        else:
            hoje = timezone.localdate()
            d1 = proximo_dia_util(hoje, 1)
            d2 = proximo_dia_util(hoje, 2)
            criar_agendamento(
                profissional=ana, espaco=sala, atletas=[joao],
                registrado_por=recep, inicio=momento(d1, 9),
                fim=momento(d1, 10), observacoes="Avaliação inicial")
            criar_agendamento(
                profissional=ana, espaco=sala, atletas=[pedro],
                registrado_por=recep, inicio=momento(d1, 10, 30),
                fim=momento(d1, 11, 30))
            criar_agendamento(
                profissional=bruno, espaco=quadra, atletas=[carla],
                registrado_por=recep, inicio=momento(d2, 15),
                fim=momento(d2, 16), modalidade="grupo",
                limite_participantes=6, equipamentos=[bola],
                observacoes="Turma de vôlei")

        dia_demo = proximo_dia_util(timezone.localdate())
        datas_demo = [dia_demo + timedelta(weeks=semana) for semana in range(3)]
        for dia in datas_demo:
            for profissional, espaco, atletas, hora, minuto, descricao, limite in (
                (ana, sala, [luiza], 8, 30, "Avaliação funcional", 1),
                (ana, sala, [pedro], 14, 0, "Acompanhamento funcional", 1),
                (bruno, quadra, [carla], 9, 30, "Treino em grupo · vagas abertas", 6),
                (bruno, quadra, [joao, carla], 16, 0, "Circuito em grupo · turma lotada", 2),
            ):
                inicio = momento(dia, hora, minuto)
                fim = inicio + timedelta(minutes=30)
                if Agendamento.objects.filter(
                    profissional=profissional, inicio__lt=fim, fim__gt=inicio,
                ).exclude(situacao=Agendamento.Situacao.CANCELADO).exists():
                    continue
                criar_agendamento(
                    profissional=profissional, espaco=espaco, atletas=atletas,
                    registrado_por=recep, inicio=inicio, fim=fim,
                    modalidade=(Agendamento.Modalidade.GRUPO if limite > 1
                                else Agendamento.Modalidade.INDIVIDUAL),
                    observacoes=descricao, limite_participantes=limite,
                )

        self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
        self.stdout.write(
            "Datas para a demonstração: " + ", ".join(
                dia.strftime("%d/%m/%Y") for dia in datas_demo
            )
        )
        self.stdout.write(
            f"Logins (senha {SENHA}): recepcao, resp_marta, demo_pedro, demo_luiza, prof_ana, prof_bruno")
        self.stdout.write(
            "Aula experimental: use o atleta 'Visitante Experimental' "
            "(registrado_por = a recepcionista).")
