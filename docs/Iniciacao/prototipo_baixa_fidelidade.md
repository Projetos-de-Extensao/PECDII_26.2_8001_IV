# Protótipo de Baixa Fidelidade — Playmakerz

## Tela 1 — Login e Cadastro

### Login

```plantuml
@startsalt

{+
    {* <b>Playmakerz - Login}

    {
        <b>Acesse sua conta
    }

    {
        @ E-mail: | "exemplo@gmail.com           "
        <&key> Senha: | "********                    "
    }

    {
        [<&account-login> Entrar]
        [Esqueci minha senha]
    }

    ..

    {
        Ainda não possui uma conta?
        [<&person> Criar conta]
    }

    --

    {
        Login com: | [Google]
    }
}

@endsalt
```
Observação: cada usuário deverá ter acesso somente às informações necessárias para sua função, visando proteger dados pessoais e sensíveis.

### Cadastro
```plantuml
@startsalt

{+
    {* <b>Playmakerz - Cadastro}

    {
        <b>Crie sua conta
    }

    {
        <&person> Nome: | "                         "
        @ E-mail: | "exemplo@gmail.com        "
        <&phone> Telefone: | "(00) 00000-0000          "
        <&key> Senha: | "********                 "
        <&key> Confirmar senha: | "********                 "
        Tipo de usuário: | ^Atleta^
    }

    [X] Concordo com os Termos de Uso

    ..

    {
        [<&person> Criar conta] | [Voltar]
    }
}

@endsalt
```
Observação: para atletas menores de idade, deverá ser considerada a associação da conta a um pai ou responsável.

Observação: o cadastro e as permissões de determinados perfis, principalmente funcionários e profissionais, poderão depender de autorização da administração.

---

## Tela 2 — Informações de Agendamento
```plantuml
@startsalt

{+
    {* <b>Playmakerz - Agendamentos}

    {
        <b>Buscar agendamentos
    }

    {
        <&calendar> Dia: | "dd/mm/aaaa"
        <&person> Profissional: | "Carlos Mendes     "
    }

    {
        [Filtrar] | [Limpar filtros]
    }

    --

    {
        <b>Lista de agendamentos
    }

    {
        Dia: 15/09/2026
        Horário: 08:00 - 09:00
        Profissional: Carlos Mendes
        [Ver detalhes]
    }

    --

    {
        Dia: 15/09/2026
        Horário: 09:00 - 10:00
        Profissional: Carlos Mendes
        [Ver detalhes]
    }

    --

    {
        Dia: 16/09/2026
        Horário: 14:00 - 15:00
        Profissional: Carlos Mendes
        [Ver detalhes]
    }

    --

    {
        Dia: 16/09/2026
        Horário: 16:00 - 17:00
        Profissional: Carlos Mendes
        [Ver detalhes]
    }
}

@endsalt
```
### Verificação do Agendamento

Antes da confirmação, o sistema deverá verificar se os elementos envolvidos no atendimento estão disponíveis durante o período selecionado.

Verificação: disponibilidade do atleta  
Verificação: disponibilidade do profissional  
Verificação: disponibilidade do espaço  
Verificação: disponibilidade dos equipamentos selecionados  
Verificação: existência de bloqueios por manutenção  
Mensagem: informar quando o agendamento estiver disponível  
Mensagem de conflito: informar quando algum atleta, profissional, espaço ou equipamento já estiver associado a outro agendamento no mesmo período ou estiver indisponível  

Botão: Confirmar agendamento

Observação: o sistema deverá impedir reservas duplicadas ou com conflito de horário.

Observação: após a confirmação, o agendamento deverá ficar disponível para consulta pelos usuários autorizados de acordo com seus respectivos perfis.

Observação: atletas e responsáveis deverão visualizar apenas os agendamentos relacionados a eles, enquanto profissionais deverão consultar sua própria agenda. Perfis administrativos poderão possuir acesso mais amplo conforme suas permissões.

Observação: o sistema deverá permitir posteriormente o acompanhamento do status do atendimento, incluindo presença, falta ou cancelamento, conforme previsto no escopo do projeto.

## Referências

> Material Design Color Tool. Disponível em:  https://material.io/resources/color/#!/?view.left=0&view.right=0

> PMI. Um guia do conhecimento em gerenciamento de projetos. Guia PMBOK® 5a. ed. EUA: Project Management Institute, 2013.

> Ferramenta Figma. Disponível em https://www.figma.com

## Autor(es)

| Data     | Versão | Descrição                            | Autor(es)                                                                            |
| -------- | ------- | -------------------------------------- | ------------------------------------------------------------------------------------ |
|01/09/26|1.0| Criação do documento|Marcos Martins|

