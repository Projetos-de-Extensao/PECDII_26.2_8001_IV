---
id: brainstorm
title: Brainstorm
---
 
---
id: brainstorm
title: Brainstorm
---

## Introdução

<p align="justify">
O brainstorm é uma técnica de elicitação de requisitos que consiste em reunir a equipe para discutir tópicos gerais do projeto apresentados no documento de problema de negócio. Durante a atividade, o diálogo é incentivado e as críticas são evitadas, permitindo que todos contribuam com suas ideias.
</p>

## Metodologia

<p align="justify">
A equipe se reuniu por meio de reunião, em 08/09/2026, com início às 12:30 e término às 13:30. A moderação foi realizada por Daniel Gusmão, que conduziu a discussão com perguntas previamente elaboradas. As contribuições foram consolidadas neste documento, com foco na gestão de alunos, profissionais, agendamentos e acompanhamento da evolução dos alunos de um centro de treinamento.
</p>

## Brainstorm

## Versão 1.0

## Perguntas

### 1. Qual o objetivo principal da aplicação?

<p align="justify">
<b>Síntese das ideias:</b> A aplicação deve centralizar a gestão dos horários de alunos e profissionais do centro de treinamento, além de permitir o registro e a consulta de informações sobre a evolução dos alunos. O objetivo principal é apoiar os profissionais no acompanhamento do desenvolvimento de cada aluno, por meio do histórico de atendimentos, avaliações e relatórios.
</p>

---

### 2. Como será o processo para agendamento de horário?

<p align="justify">
<b>Síntese das ideias:</b> O usuário deverá realizar login, consultar os profissionais disponíveis, selecionar o profissional desejado e verificar os horários livres em sua agenda. Após escolher o horário e confirmar a solicitação, o sistema deverá registrar o agendamento, enviar uma confirmação e emitir lembretes antes do atendimento.
</p>

**Fluxo proposto:**

Login → Consulta de profissionais → Seleção do profissional → Consulta de horários disponíveis → Escolha do horário → Confirmação do agendamento → Envio de confirmação e lembretes.

---

### 3. Como será o processo para cadastrar um novo aluno?

<p align="justify">
<b>Síntese das ideias:</b> O cadastro deverá incluir a coleta e a verificação dos documentos necessários, a autorização dos responsáveis quando aplicável e a apresentação dos exames médicos exigidos pelo centro. Após a conferência das informações e a resolução das pendências, o cadastro poderá ser concluído.
</p>

**Fluxo proposto:**

Coleta e verificação de documentos → Coleta de autorização do responsável, quando aplicável → Solicitação e apresentação dos exames médicos exigidos → Conferência das informações → Conclusão do cadastro.

---

### 4. Como será realizado o acompanhamento da evolução do aluno?

<p align="justify">
<b>Síntese proposta para validação:</b> Os profissionais poderão registrar avaliações, observações e resultados relacionados aos objetivos de cada aluno. Essas informações deverão compor um histórico que permita acompanhar mudanças ao longo do tempo e apoiar o planejamento dos próximos atendimentos.
</p>

<p align="justify">
Os critérios utilizados para avaliar a evolução deverão ser definidos pela equipe conforme as modalidades oferecidas e os objetivos dos alunos.
</p>

---

### 5. Como será a geração de relatórios?

<p align="justify">
<b>Síntese das ideias:</b> O sistema deverá permitir que os profissionais gerem relatórios para acompanhar a evolução dos alunos, conforme suas necessidades.
</p>

<p align="justify">
<b>Detalhamento proposto para validação:</b> Os relatórios poderão ser filtrados por aluno e período, apresentando avaliações, observações e resultados registrados. O conteúdo e o formato dos relatórios deverão ser definidos com os profissionais do centro.
</p>

---

### 6. Quais informações seriam interessantes para o aluno ou responsável?

<p align="justify">
<b>Síntese das ideias:</b> O aluno ou responsável deverá ter acesso a lembretes de agendamento, notificações essenciais e informações financeiras relacionadas aos serviços contratados.
</p>

**Informações sugeridas:**

- **Agendamentos:** datas, horários e profissionais responsáveis pelos próximos atendimentos.
- **Lembretes:** avisos prévios sobre os atendimentos agendados.
- **Notificações essenciais:** confirmações, alterações ou cancelamentos de atendimentos e pendências cadastrais.
- **Comunicados gerais:** informações sobre o funcionamento e as atividades do centro.
- **Financeiro:** valores, vencimentos e situação dos pagamentos.

---

### Requisitos elicitados

Os requisitos abaixo consolidam as ideias apresentadas. Os itens identificados como propostas deverão ser validados pela equipe antes de integrarem o escopo.

| ID | Descrição |
|----|-----------|
| BS01 | O sistema deve permitir a autenticação dos usuários. |
| BS02 | O sistema deve permitir o cadastro de alunos. |
| BS03 | O sistema deve permitir o registro e a verificação dos documentos necessários ao cadastro. |
| BS04 | O sistema deve permitir o registro da autorização dos responsáveis, quando aplicável. |
| BS05 | O sistema deve permitir o controle da entrega dos exames médicos exigidos pelo centro. |
| BS06 | O sistema deve permitir a consulta dos profissionais disponíveis para atendimento. |
| BS07 | O sistema deve permitir a consulta dos horários disponíveis de cada profissional. |
| BS08 | O sistema deve permitir o agendamento de um atendimento com o profissional e o horário selecionados. |
| BS09 | O sistema deve enviar confirmações de agendamento. |
| BS10 | O sistema deve enviar lembretes dos atendimentos agendados. |
| BS11 | O sistema deve disponibilizar notificações essenciais e comunicados aos alunos ou responsáveis. |
| BS12 | O sistema deve permitir que os profissionais gerem relatórios para acompanhar a evolução dos alunos. |
| BS13 | O sistema deve disponibilizar informações financeiras ao aluno ou responsável. |
| BS14 | **Proposta:** o sistema deve permitir que os profissionais registrem avaliações, observações e resultados dos alunos. |
| BS15 | **Proposta:** o sistema deve permitir a consulta do histórico de evolução do aluno e a geração de relatórios com filtros por aluno e período. |

## Conclusão

<p align="justify">
A aplicação da técnica de brainstorm permitiu identificar os primeiros requisitos relacionados ao cadastro de alunos, ao agendamento de atendimentos, à comunicação com alunos e responsáveis e ao acompanhamento da evolução dos alunos. As propostas de detalhamento deverão ser validadas com os envolvidos, especialmente quanto aos critérios de evolução, ao conteúdo dos relatórios e às funcionalidades financeiras.
</p>

## Referências Bibliográficas

> BARBOSA, S. D. J.; DA SILVA, B. S. Interação humano-computador. Elsevier, 2010.

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
|------|--------|-----------|-----------|
| [08/09/2026] | 1.0 | Criação do documento | Daniel Gusmão |
