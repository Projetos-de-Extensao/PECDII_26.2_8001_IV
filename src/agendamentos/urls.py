from django.urls import path

from . import views

app_name = "agendamentos"

urlpatterns = [
    path("", views.lista_agendamentos, name="lista"),
    path("novo/", views.novo_agendamento, name="novo"),
    path("horarios/", views.horarios_profissional, name="horarios"),
    path("<int:agendamento_id>/", views.detalhe_agendamento, name="detalhe"),
    path(
        "<int:agendamento_id>/cancelar/",
        views.cancelar_agendamento_view,
        name="cancelar",
    ),
    path(
        "participacoes/<int:participacao_id>/cancelar/",
        views.cancelar_participacao_view,
        name="cancelar_participacao",
    ),
]
