---
id: levantamento de requisitos
title: Levantamento de Requisitos
---
# **06 - Levantamento de Requisitos e Caso de Uso**

**Sistema:** Sistema de Gestão da Playmakerz*)

---

## **1. Identificação dos Stakeholders**

- **Gestores:** Responsáveis pela academia. Definem quem pode acessar o quê e acompanham a ocupação dos espaços.
- **Recepção:** Funcionários que organizam os horários e fazem os agendamentos.
- **Coordenadores:** Acompanham a agenda dos profissionais e dos atletas.
- **Treinadores e profissionais:** Conduzem os atendimentos e consultam a própria agenda.
- **Manutenção:** Funcionários que avisam quando um espaço ou equipamento não pode ser usado.
- **Atletas:** Pessoas atendidas pela Playmakerz.
- **Pais ou responsáveis:** Acompanham os agendamentos e autorizam os atletas menores de idade.
- **Pró-Reitoria Acadêmica:** Stakeholder do projeto de extensão.

---

### **2. Requisitos Funcionais**

| ID   | Descrição                                                                    | Prioridade |
| ---- | ------------------------------------------------------------------------------ | ---------- |
| RF01 | O usuário deve conseguir entrar no sistema com e-mail e senha. | Alta |
| RF02 | O sistema deve permitir cadastrar atletas, responsáveis, profissionais e funcionários. | Alta 
| RF03 | O cadastro de profissionais e funcionários deve depender de autorização da administração.  Média |
| RF04 | O atleta menor de idade deve ser associado a um pai ou responsável. | Alta |
| RF05 | A recepção deve registrar os documentos, a autorização do responsável e a entrega dos exames médicos do atleta. | Média |
| RF06 | O sistema deve permitir cadastrar espaços e equipamentos. | Alta |
| RF07 | O funcionário da manutenção deve conseguir bloquear um espaço ou equipamento por um período. | Média |
| RF08 | O usuário deve conseguir consultar os profissionais e os horários livres de cada um. | Alta |
| RF09 | O sistema deve permitir criar agendamentos individuais ou em grupo, com atleta(s), profissional, espaço e equipamentos. | Alta |
| RF10 | O sistema deve verificar conflitos de horário (atleta, profissional, espaço, equipamento e manutenção) antes de confirmar. | Alta |
| RF11 | O sistema deve permitir agendamentos recorrentes. | Média |
| RF12 | O sistema deve registrar presença, falta e cancelamento de cada agendamento. | Média |
| RF13 | O sistema deve enviar confirmação, lembretes e avisos sobre os agendamentos. | Média |
| RF14 | O sistema deve permitir consultar a ocupação dos espaços. | Baixa |
| RF15 | Cada usuário deve ver só o que o seu perfil permite (atleta e responsável veem só os próprios agendamentos, profissional vê a própria agenda). | Alta |
| RF16 | O profissional deve conseguir registrar avaliações e observações do atleta e gerar relatório por atleta e período. (proposta, precisa ser validada) | Baixa |

### **3. Requisitos Não Funcionais**

- **Performance:** A verificação de conflito de horário deve responder em poucos segundos, para não atrapalhar a recepção.
- **Segurança:** Os dados seguem a LGPD. Cada pessoa tem conta individual (sem senha compartilhada), o acesso é limitado pelo perfil e os dados de menores de idade recebem atenção especial. Alterações importantes devem ficar registradas.
- **Usabilidade:** A interface deve ser simples, para a recepção conseguir agendar sem treinamento longo.
- **Portabilidade:** O sistema é web e deve funcionar pelo navegador.

---

### **4. Exemplo de Caso de Uso**

#### **UC01 - Realizar Agendamento**

- **Atores:** Recepção, Sistema.
- **Pré-condição:** Usuário está logado e tem permissão para agendar. Atleta, profissional, espaço e equipamentos já estão cadastrados.
- **Fluxo Principal:**
    1. Usuário escolhe o tipo de agendamento (individual ou em grupo).
    2. Usuário seleciona o(s) atleta(s).
    3. Usuário seleciona o profissional responsável.
    4. Usuário informa a data e o horário de início e término.
    5. Usuário seleciona o espaço e os equipamentos.
    6. Usuário escolhe se o agendamento é único ou recorrente.
    7. Usuário clica em "Verificar disponibilidade".
    8. Sistema verifica atleta, profissional, espaço, equipamentos e bloqueios de manutenção.
    9. Sistema informa que está tudo disponível e o usuário confirma.
    10. Sistema registra o agendamento e envia a confirmação.
- **Fluxos Alternativos:**
    - **FA1:** Conflito de horário → Sistema informa qual item já está ocupado e pede outro horário ou outro item.
    - **FA2:** Espaço ou equipamento em manutenção → Sistema informa que está indisponível e pede outra escolha.
- **Pós-condição:** Agendamento registrado e visível para os usuários autorizados. Lembretes programados.

---

### **5. Protótipo **

O protótipo de baixa fidelidade já foi feito na Iniciação:
 
- **Tela 1:** Login e cadastro.
- **Tela 2:** Informações de agendamento, com a verificação de disponibilidade.
Veja em [Prototipagem Baixa Fidelidade](../Iniciacao/prototipo_baixa_fidelidade.md).

---

### **6. Validação**

- **Responsáveis da Playmakerz:** Confirmar quais perfis de usuário existem e o que cada um pode fazer, já que as informações da academia vieram do Instagram.
- **Financeiro:** Confirmar com o cliente e com o grupo se informações financeiras entram no sistema.
- **Evolução do aluno:** Validar com os profissionais o que deve ter nas avaliações e nos relatórios (RF16).
- **Grupo:** Revisar as prioridades dos requisitos.