---
id: levantamento de requisitos
title: Levantamento de Requisitos
---
# **06 - Levantamento de Requisitos e Caso de Uso**

**Sistema:** Sistema de Gestão da Playmakerz

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

| ID   | Descrição | Prioridade | Situação | Observação sobre o código |
| ---- | --------- | ---------- | -------- | ------------------------- |
| RF01 | O usuário deve conseguir entrar no sistema com e-mail e senha. | Alta | Parcial | Login do Django com usuário e senha, não por e-mail. |
| RF02 | O sistema deve permitir cadastrar atletas, responsáveis, profissionais e funcionários. | Alta | Implementado | Cadastros no Django admin. Atletas também pela API e pelo cadastro rápido de interessados. |
| RF03 | O cadastro de profissionais e funcionários deve depender de autorização da administração. | Média | Parcial | Só quem tem permissão no Django admin cadastra profissionais e funcionários. Não há fluxo de autorização. |
| RF04 | O atleta menor de idade deve ser associado a um pai ou responsável. | Alta | Parcial | O vínculo existe. A exigência vale na hora de agendar, não no cadastro. |
| RF05 | A recepção deve registrar os documentos, a autorização do responsável e a entrega dos exames médicos do atleta. | Média | Planejado | Sem registro de documentos, autorização ou exames. |
| RF06 | O sistema deve permitir cadastrar espaços e equipamentos. | Alta | Implementado | API `/api/espacos/` e `/api/equipamentos/` e Django admin. |
| RF07 | O funcionário da manutenção deve conseguir bloquear um espaço ou equipamento por um período. | Média | Planejado | Sem bloqueio por manutenção. |
| RF08 | O usuário deve conseguir consultar os profissionais e os horários livres de cada um. | Alta | Implementado | Horários livres do profissional na tela de novo agendamento (`/agendamentos/horarios/`). |
| RF09 | O sistema deve permitir criar agendamentos individuais ou em grupo, com atleta(s), profissional, espaço e equipamentos. | Alta | Implementado | Agendamentos individuais e em grupo, pela tela e pela API. |
| RF10 | O sistema deve verificar conflitos de horário (atleta, profissional, espaço, equipamento e manutenção) antes de confirmar. | Alta | Parcial | Atleta, profissional, espaço e equipamento são verificados. Manutenção ainda não. |
| RF11 | O sistema deve permitir agendamentos recorrentes. | Média | Planejado | Sem recorrência. |
| RF12 | O sistema deve registrar presença, falta e cancelamento de cada agendamento. | Média | Parcial | Cancelamento implementado. Presença e falta existem só no modelo. |
| RF13 | O sistema deve enviar confirmação, lembretes e avisos sobre os agendamentos. | Média | Planejado | Sem envio de mensagens. |
| RF14 | O sistema deve permitir consultar a ocupação dos espaços. | Baixa | Planejado | Sem tela de ocupação. |
| RF15 | Cada usuário deve ver só o que o seu perfil permite (atleta e responsável veem só os próprios agendamentos, profissional vê a própria agenda). | Alta | Planejado | Hoje a interface exige acesso de equipe e a API exige login. Não há visão por perfil. |
| RF16 | O profissional deve conseguir registrar avaliações e observações do atleta e gerar relatório por atleta e período. (proposta, precisa ser validada) | Baixa | Planejado | Sem avaliações e relatórios. |
| RF17 | O sistema deve permitir remarcar um agendamento, liberando os recursos antigos e avisando os envolvidos. | Média | Planejado | Sem edição de agendamento: é preciso cancelar e criar outro. |
| RF18 | O gestor deve conseguir consultar o registro de alterações importantes do sistema. | Média | Planejado | Sem registro geral de alterações. |
| RF19 | O sistema deve permitir agendar uma aula experimental para um interessado, uma única vez por pessoa, registrada por um recepcionista. (incluído a partir do código, precisa ser validado) | Média | Implementado | Cadastro rápido de interessado maior de 18 anos, na tela de novo agendamento. |

A situação de cada requisito foi conferida com o código em 10/11/2026. **Implementado** significa que o fluxo existe e tem testes automatizados. **Parcial** significa que parte do fluxo existe. **Planejado** significa que ainda não existe. A situação de cada caso de uso está em [Casos de Uso](casos_de_uso.md).

### **3. Requisitos Não Funcionais**

- **Performance:** A verificação de conflito de horário deve responder em poucos segundos, para não atrapalhar a recepção.
- **Segurança:** Os dados seguem a LGPD. Cada pessoa tem conta individual (sem senha compartilhada), o acesso é limitado pelo perfil e os dados de menores de idade recebem atenção especial. Alterações importantes devem ficar registradas.
- **Usabilidade:** A interface deve ser simples, para a recepção conseguir agendar sem treinamento longo.
- **Portabilidade:** O sistema é web e deve funcionar pelo navegador.

---

### **4. Casos de Uso**

Os casos de uso do sistema estão em [Casos de Uso](casos_de_uso.md), com atores, fluxo principal, fluxos alternativos e de exceção. O caso de uso central é o **Criar agendamento individual**, que reúne atleta, profissional, espaço e equipamento e verifica os conflitos de horário antes de confirmar.

---

### **5. Protótipo**

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