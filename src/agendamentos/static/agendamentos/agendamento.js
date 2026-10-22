document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#agendamento-form");
    if (!form) return;

    const profissional = form.querySelector("#id_profissional");
    const data = form.querySelector("#id_data");
    const inicio = form.querySelector("#id_inicio");
    const fim = form.querySelector("#id_fim");
    const grupo = form.querySelector("#id_agendamento_grupo");
    const modalidade = form.querySelector("#id_modalidade");
    const limite = form.querySelector("#id_limite_participantes");
    const grade = form.querySelector("#schedule-grid");
    const mensagem = form.querySelector("#schedule-message");
    const seletor = form.querySelector("#schedule-picker");
    const novosCampos = form.querySelector("#new-activity-fields");
    const avisoGrupo = form.querySelector("#group-join-note");
    const campoLimite = form.querySelector("#limit-field");
    const botaoEnviar = form.querySelector("#submit-button");
    const novoAtleta = form.querySelector("#id_novo_atleta");
    const aulaExperimental = form.querySelector("#id_aula_experimental");
    const botaoExperimental = form.querySelector("#experimental-mode-button");
    const atletasExistentes = form.querySelector("#existing-athlete-fields");
    const camposNovoAtleta = form.querySelector("#quick-athlete-fields");

    function modoExperimentalAtivo() {
        return ["true", "True", "1", "on"].includes(novoAtleta.value);
    }

    function atualizarCadastroRapido() {
        const cadastrando = modoExperimentalAtivo();
        atletasExistentes.classList.toggle("is-hidden", cadastrando);
        camposNovoAtleta.classList.toggle("is-hidden", !cadastrando);
        aulaExperimental.value = cadastrando ? "true" : "false";
        botaoExperimental.classList.toggle("is-active", cadastrando);
        botaoExperimental.setAttribute("aria-pressed", String(cadastrando));
    }

    function atualizarModalidade() {
        const grupoNovo = modalidade.value === "grupo";
        campoLimite.classList.toggle("is-hidden", !grupoNovo);
        if (!grupoNovo) limite.value = "1";
        if (grupoNovo && Number(limite.value) < 2) limite.value = "2";
    }

    function configurarEntradaEmGrupo(entrando) {
        novosCampos.classList.toggle("is-hidden", entrando);
        avisoGrupo.classList.toggle("is-hidden", !entrando);
        botaoEnviar.textContent = entrando
            ? "Inscrever na atividade"
            : "Criar agendamento";
    }

    function limparSelecao() {
        inicio.value = "";
        fim.value = "";
        grupo.value = "";
        grade.querySelectorAll(".schedule-slot-selected").forEach((item) => {
            item.classList.remove("schedule-slot-selected");
        });
        configurarEntradaEmGrupo(false);
    }

    function selecionarBloco(botao, horario) {
        limparSelecao();
        botao.classList.add("schedule-slot-selected");
        inicio.value = horario.inicio;
        fim.value = horario.fim;
        grupo.value = horario.agendamento_id || "";
        configurarEntradaEmGrupo(horario.tipo === "grupo");
    }

    function criarBotao(horario, inicioSelecionado) {
        const botao = document.createElement("button");
        botao.type = "button";
        botao.className = `schedule-slot schedule-slot-${horario.tipo}`;
        botao.disabled = !horario.disponivel;

        const hora = document.createElement("strong");
        hora.textContent = horario.rotulo;
        botao.appendChild(hora);

        const detalhe = document.createElement("small");
        if (horario.tipo === "grupo") {
            detalhe.textContent = `${horario.inscritos}:${horario.limite}`;
            botao.title = horario.disponivel
                ? "Atividade em grupo com vagas"
                : "Atividade em grupo lotada";
        } else if (horario.tipo === "individual") {
            detalhe.textContent = "Ocupado";
            botao.title = "Horário ocupado";
        } else {
            detalhe.textContent = "Disponível";
        }
        botao.appendChild(detalhe);

        if (horario.disponivel) {
            botao.addEventListener("click", () => selecionarBloco(botao, horario));
        }
        if (horario.inicio === inicioSelecionado && horario.disponivel) {
            selecionarBloco(botao, horario);
        }
        return botao;
    }

    async function carregarHorarios() {
        const inicioSelecionado = inicio.value;
        limparSelecao();
        grade.replaceChildren();

        if (!profissional.value || !data.value) {
            mensagem.textContent = "Selecione um profissional e uma data para consultar os horários.";
            mensagem.classList.remove("is-hidden");
            return;
        }

        mensagem.textContent = "Consultando horários...";
        mensagem.classList.remove("is-hidden");

        const parametros = new URLSearchParams({
            profissional: profissional.value,
            data: data.value,
        });

        try {
            const resposta = await fetch(`${seletor.dataset.url}?${parametros}`);
            const conteudo = await resposta.json();
            if (!resposta.ok) throw new Error(conteudo.erro || "Falha ao consultar horários.");

            if (!conteudo.horarios.length) {
                mensagem.textContent = "O profissional não possui disponibilidade nessa data.";
                return;
            }

            mensagem.classList.add("is-hidden");
            conteudo.horarios.forEach((horario) => {
                grade.appendChild(criarBotao(horario, inicioSelecionado));
            });
        } catch (erro) {
            mensagem.textContent = erro.message;
        }
    }

    profissional.addEventListener("change", carregarHorarios);
    data.addEventListener("change", carregarHorarios);
    modalidade.addEventListener("change", atualizarModalidade);
    botaoExperimental.addEventListener("click", () => {
        novoAtleta.value = modoExperimentalAtivo() ? "false" : "true";
        atualizarCadastroRapido();
    });
    atualizarModalidade();
    atualizarCadastroRapido();
    carregarHorarios();
});
