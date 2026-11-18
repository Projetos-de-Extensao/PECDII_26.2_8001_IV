from django.contrib.auth import views
from django.urls import path

from agendamentos.portal import decidir_reserva, minhas_aulas, reservar_aula

urlpatterns = [
    path("", minhas_aulas, name="portal"),
    path("reservar/", reservar_aula, name="portal_reserva"),
    path("solicitacoes/<int:pk>/decidir/", decidir_reserva, name="portal_decidir_reserva"),
    path("entrar/", views.LoginView.as_view(
        template_name="agendamentos/portal_login.html"
    ), name="portal_login"),
    path("sair/", views.LogoutView.as_view(), name="portal_logout"),
]
