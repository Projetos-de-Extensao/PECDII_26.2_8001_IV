---
id: documento_de_visao
title: Documento de Visão
---

# Documento de Visão — Sistema de Gestão da Playmakerz

**Projeto:** Playmakerz — Sistema de Gestão Esportiva  
**Versão:** 0.1
**Data de referência:** 10/09/2026

## 1. Introdução

Este documento apresenta a visão do sistema de gestão esportiva proposto para a **Playmakerz**, centro de treinamento voltado à alta performance esportiva, localizado na Barra da Tijuca, Rio de Janeiro. Seu objetivo é alinhar a equipe de desenvolvimento e os interessados quanto ao problema tratado, aos objetivos, ao público-alvo, ao escopo e às restrições da solução.

As informações iniciais sobre a rotina da Playmakerz foram obtidas por pesquisa pública, inclusive em redes sociais, conforme registrado na documentação do projeto.

## 2. Descrição do problema

### 2.1 Contexto

O funcionamento de um centro de treinamento envolve a coordenação simultânea de atletas, profissionais, espaços e equipamentos. Um atendimento pode depender da disponibilidade de todos esses elementos, e seu agendamento precisa considerar também limites de capacidade, a participação em grupos e situações de cancelamento.

A organização dessas informações sem um controle integrado pode produzir conflitos de horário, duplicidade de reservas, dificuldades de acompanhamento e retrabalho operacional. A presença de crianças e adolescentes entre os atletas reforça a necessidade de atenção ao tratamento de dados pessoais e aos vínculos com responsáveis.

### 2.2 Síntese do problema

| Elemento | Descrição |
| --- | --- |
| **Problema** | Dificuldade de centralizar os registros e coordenar, no mesmo atendimento, a disponibilidade de atletas, profissionais, espaços e equipamentos. |
| **Impactados** | Recepção, gestão, coordenação, profissionais, atletas e responsáveis. |
| **Consequências potenciais** | Choques de agenda, reservas incompatíveis, retrabalho, baixa visibilidade da ocupação e acesso inadequado a informações pessoais. |
| **Solução proposta** | Um sistema integrado para cadastrar recursos, consultar disponibilidade, administrar agendamentos e aplicar automaticamente regras de conflito e capacidade. |

As consequências descritas são riscos operacionais identificados pela equipe, **não indicadores de ocorrências medidas na Playmakerz**.

### 2.3 Declaração de visão

> Para a equipe da Playmakerz que precisa organizar atendimentos e utilizar de forma coordenada profissionais, atletas, espaços e equipamentos, o sistema de gestão esportiva será uma aplicação que centralizará essas informações, facilitará o acompanhamento da agenda e verificará conflitos antes da confirmação dos atendimentos.

## 3. Objetivos

### 3.1 Objetivo geral

Apoiar a gestão operacional da Playmakerz por meio de uma solução que integre cadastros, disponibilidade e agendamento de atendimentos esportivos, buscando maior organização, previsibilidade e segurança no uso dos recursos.

### 3.2 Objetivos específicos

- Centralizar os cadastros de atletas, responsáveis, profissionais, funcionários, espaços e equipamentos.
- Consultar a disponibilidade dos profissionais e permitir agendamentos individuais e em grupo.
- Verificar previamente conflitos que envolvam profissionais, atletas, equipamentos e a capacidade dos espaços.
- Permitir o acompanhamento e o cancelamento de agendamentos e participações, preservando os registros necessários.
- Tratar de forma adequada os agendamentos de atletas menores de idade, exigindo responsável vinculado quando aplicável.
- Evoluir o controle de acesso para que cada perfil consulte e altere somente informações compatíveis com suas atribuições.

## 4. Stakeholders e usuários

| Público | Necessidades e responsabilidades previstas |
| --- | --- |
| **Gestores** | Acompanhar a operação e administrar autorizações e recursos. |
| **Recepção** | Consultar horários, cadastrar atletas e registrar, inscrever ou cancelar atendimentos. |
| **Profissionais e treinadores** | Consultar a própria disponibilidade e seus atendimentos. |
| **Atletas** | Acompanhar os próprios atendimentos e informações cadastrais. |
| **Pais ou responsáveis** | Acompanhar e autorizar atendimentos de menores de idade. |
## 5. Escopo e recursos do produto

O sistema proposto terá como principal finalidade centralizar a gestão dos atendimentos esportivos da Playmakerz, integrando informações sobre atletas, profissionais, espaços, equipamentos e agendamentos.

A solução deverá oferecer recursos que facilitem a organização da rotina administrativa, a consulta de horários e a utilização adequada dos recursos disponíveis.

### 5.1 Funcionalidades principais

| Funcionalidade | Descrição | Requisitos relacionados |
| --- | --- | --- |
| Autenticação de usuários | Permitir o acesso ao sistema mediante identificação e autenticação, protegendo as operações administrativas. | RF01, RF15 |
| Gerenciamento de cadastros | Possibilitar o cadastro e a manutenção das informações de atletas, responsáveis, profissionais, funcionários, espaços e equipamentos. | RF02, RF03, RF04, RF06 |
| Consulta de disponibilidade | Permitir a consulta dos profissionais e de seus horários disponíveis, considerando os períodos de atendimento cadastrados. | RF08 |
| Agendamentos individuais | Permitir a criação de atendimentos individuais, associando um atleta a um profissional, espaço, data e horário. | RF09 |
| Agendamentos em grupo | Permitir a criação de atividades coletivas, com definição de capacidade e controle da quantidade de participantes. | RF09 |
| Inscrição em atividades existentes | Possibilitar a inclusão de atletas em atividades em grupo que ainda possuam vagas disponíveis. | RF09 |
| Aulas experimentais | Permitir o registro de aulas experimentais e o cadastro de interessados, respeitando os critérios estabelecidos para essa modalidade de atendimento. | RF02, RF09 |
| Verificação de conflitos | Verificar a disponibilidade dos atletas, profissionais, espaços e equipamentos antes da confirmação de um agendamento. | RF10 |
| Consulta da agenda | Disponibilizar uma visão organizada dos agendamentos, com informações sobre horários, profissionais, participantes, espaços e situação dos atendimentos. | RF08, RF09, RF15 |
| Cancelamento de agendamentos | Permitir o cancelamento de atendimentos completos ou de participações individuais, registrando as informações necessárias para o acompanhamento da operação. | RF12 |

### 5.2 Fluxo principal de utilização

O fluxo de utilização do sistema será estruturado para facilitar o trabalho da recepção e reduzir a quantidade de etapas necessárias para registrar um atendimento.

Inicialmente, o funcionário deverá acessar o sistema e consultar os profissionais disponíveis. Após selecionar o profissional e a data desejada, poderá verificar os horários de atendimento e identificar as possibilidades de agendamento.

Em seguida, o funcionário deverá selecionar o atleta, definir a modalidade do atendimento e informar os demais recursos necessários, incluindo espaço e equipamentos, quando aplicável.

Antes da confirmação, o sistema deverá verificar as regras de disponibilidade, capacidade e conflito de horários. Caso alguma condição não seja atendida, deverá informar o motivo para que os dados sejam corrigidos.

Após a confirmação, o agendamento deverá ficar disponível para consulta e acompanhamento. O sistema também deverá permitir a inscrição de novos participantes em atividades coletivas e o cancelamento de atendimentos ou participações.

### 5.3 Limites do escopo

O projeto terá como foco a organização administrativa dos atendimentos esportivos e a gestão dos recursos necessários para sua realização.

Não fazem parte do escopo principal desta proposta:

- Gestão financeira, cobranças e processamento de pagamentos;
- Administração de planos, mensalidades e créditos;
- Prontuários clínicos e acompanhamento médico;
- Integração com catracas e sistemas de controle físico de acesso;
- Análises avançadas de desempenho esportivo.

Essas áreas possuem necessidades próprias e poderão ser avaliadas separadamente, caso sejam identificadas como relevantes para a organização.

## 6. Regras e restrições essenciais

Para garantir a consistência das informações e a utilização adequada dos recursos, o sistema deverá considerar as seguintes regras de negócio:

- **Atletas e responsáveis:** os atletas deverão possuir cadastro ativo e data de nascimento válida para realizar agendamentos. Atletas menores de 18 anos deverão estar vinculados a um responsável.

- **Horários de atendimento:** os agendamentos deverão respeitar a disponibilidade semanal dos profissionais e utilizar horários organizados em intervalos de 30 minutos. As janelas de atendimento consideradas serão das 07h às 12h e das 13h às 20h.

- **Agendamentos individuais:** cada atendimento individual deverá possuir exatamente um atleta e um profissional responsável.

- **Atividades em grupo:** as atividades coletivas deverão possuir limite mínimo de duas vagas, respeitando a capacidade do espaço utilizado. Uma atividade poderá ser criada com apenas um participante inicialmente inscrito.

- **Disponibilidade dos participantes:** um atleta ou profissional não poderá participar de atendimentos com horários conflitantes.

- **Utilização dos espaços:** diferentes atividades poderão compartilhar um espaço no mesmo período, desde que a soma das capacidades reservadas não ultrapasse o limite disponível.

- **Utilização dos equipamentos:** equipamentos associados a um atendimento não poderão ser reservados simultaneamente para atividades conflitantes.

- **Aulas experimentais:** deverão exigir as informações necessárias para identificar e contatar o interessado, além de registro por um recepcionista autorizado. O cadastro simplificado será destinado a interessados maiores de idade. O sistema deverá controlar as participações experimentais para evitar a utilização repetida indevida dessa modalidade.

- **Cancelamentos:** o sistema deverá permitir o cancelamento de agendamentos ainda não realizados e de participações individuais confirmadas. Os cancelamentos deverão preservar informações como situação, motivo e data, sem excluir o histórico do atendimento.

- **Controle de acesso:** o acesso às operações administrativas deverá exigir autenticação. A definição das permissões deverá considerar as responsabilidades de cada categoria de usuário e a necessidade de proteção das informações pessoais.

Essas regras deverão orientar a modelagem dos dados, a definição dos casos de uso e o desenvolvimento das operações de agendamento.

## 7. Requisitos não funcionais

Além das funcionalidades previstas, a solução deverá observar requisitos de qualidade que contribuam para sua segurança, confiabilidade e facilidade de utilização.

| Requisito | Diretriz |
| --- | --- |
| **Segurança e privacidade** | Proteger os dados pessoais armazenados, utilizar autenticação e considerar as disposições aplicáveis da Lei Geral de Proteção de Dados Pessoais (LGPD), com atenção especial às informações de menores de idade. |
| **Usabilidade** | Oferecer uma navegação intuitiva e fluxos objetivos para consulta e criação de agendamentos. |
| **Desempenho** | Realizar consultas de disponibilidade e verificações de conflitos em tempo adequado para não comprometer a rotina da recepção. |
| **Integridade dos dados** | Impedir registros inconsistentes, reservas conflitantes e operações parcialmente concluídas. |
| **Confiabilidade** | Preservar as informações dos agendamentos, participantes e cancelamentos, garantindo consistência nas operações realizadas. |
| **Manutenibilidade** | Organizar a aplicação de maneira modular, facilitando correções, testes e modificações nas regras de negócio. |

A arquitetura deverá favorecer a separação entre interface, processamento das regras de negócio e persistência das informações.

## 8. Premissas, riscos e pontos de validação

O planejamento considera informações obtidas por meio da pesquisa inicial e das discussões realizadas pela equipe. Algumas características da rotina operacional da Playmakerz deverão ser confirmadas com seus representantes para assegurar a adequação da solução.

| Tema | Premissa ou risco identificado | Medida proposta |
| --- | --- | --- |
| **Conhecimento da rotina operacional** | As informações públicas disponíveis podem não representar integralmente os procedimentos internos da Playmakerz. | Validar os principais fluxos de atendimento e agendamento com representantes da organização. |
| **Disponibilidade de recursos** | Conflitos entre horários, profissionais, atletas e equipamentos podem prejudicar a organização dos atendimentos. | Estabelecer verificações de disponibilidade e capacidade antes da confirmação das reservas. |
| **Gestão dos participantes** | Atividades coletivas exigem controle da quantidade de atletas inscritos e das vagas disponíveis. | Definir limites de participação e regras para inscrição e cancelamento individual. |
| **Dados de menores de idade** | O tratamento inadequado de informações pessoais pode comprometer a privacidade dos atletas. | Definir critérios de vinculação com responsáveis e cuidados específicos de acesso e armazenamento. |
| **Diferentes categorias de usuários** | Usuários com responsabilidades distintas possuem necessidades diferentes de acesso às informações. | Identificar os perfis envolvidos e suas respectivas atribuições. |
| **Facilidade de utilização** | Um processo de agendamento complexo pode gerar dificuldades operacionais e retrabalho. | Priorizar fluxos simples, mensagens claras e consultas objetivas de disponibilidade. |
| **Definição do escopo** | A inclusão de funcionalidades não essenciais pode comprometer o foco do projeto. | Priorizar a gestão de agendamentos e dos recursos diretamente relacionados aos atendimentos. |

A validação dessas premissas deverá contribuir para o refinamento dos requisitos e para a definição das prioridades de desenvolvimento.

## 9. Critérios de validação da solução

A avaliação da solução deverá considerar sua capacidade de atender aos objetivos centrais estabelecidos para o projeto.

Como critérios iniciais, propõem-se:

1. **Organização dos cadastros:** permitir o registro e a consulta das informações necessárias para identificar atletas, responsáveis, profissionais, funcionários e recursos.

2. **Consulta de disponibilidade:** apresentar os horários disponíveis dos profissionais de acordo com os períodos cadastrados.

3. **Criação de agendamentos:** permitir o registro de atendimentos individuais e coletivos com associação dos participantes e recursos necessários.

4. **Prevenção de conflitos:** impedir a confirmação de agendamentos que violem as regras de disponibilidade, capacidade ou reserva de recursos.

5. **Gerenciamento de atividades em grupo:** permitir o controle de vagas e a inscrição de participantes em atividades existentes.

6. **Tratamento de aulas experimentais:** aplicar os critérios específicos dessa modalidade, considerando os dados dos interessados e as restrições de participação.

7. **Consulta e acompanhamento:** possibilitar a visualização das informações dos atendimentos e de seus respectivos participantes.

8. **Cancelamento de atendimentos:** permitir o registro de cancelamentos, preservando as informações necessárias para consulta e acompanhamento.

9. **Segurança das informações:** exigir autenticação para operações administrativas e considerar a proteção dos dados pessoais, especialmente daqueles pertencentes a menores de idade.

## 10. Referências

Os seguintes documentos fundamentam o levantamento inicial das necessidades e a definição da visão do sistema:

- [Pesquisa — Playmakerz](pesquisa.md).
- [5W2H](5w2h.md).
- [Brainstorming](Brainstorm.md).

As informações utilizadas nesses artefatos foram consolidadas para definir o problema, os objetivos, os usuários e os principais recursos da solução proposta.