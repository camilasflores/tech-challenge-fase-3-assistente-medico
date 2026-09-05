# Assistente Médico - Tech Challenge Fase 3

Projeto da Pós Tech **IA para Devs - FIAP**, desenvolvido para o Tech Challenge
da Fase 3.

O projeto implementa um assistente de apoio à equipe médica para acompanhamento
de pacientes adultos com hipertensão. O sistema utiliza uma LLM ajustada por
fine-tuning, consulta dados sintéticos de pacientes e protocolos internos e
coordena o fluxo de decisão com LangChain e LangGraph.

> Este projeto possui finalidade exclusivamente acadêmica. O assistente não
> realiza diagnóstico nem prescrição e todas as sugestões exigem validação de
> um profissional de saúde.

## Objetivos

- realizar fine-tuning de uma LLM com perguntas e respostas médicas;
- consultar prontuários sintéticos em uma base estruturada;
- contextualizar respostas com protocolos internos;
- identificar exames pendentes e situações que exigem atenção;
- impedir prescrições ou condutas autônomas;
- apresentar as fontes utilizadas nas respostas;
- registrar as etapas em logs para auditoria.

## Arquitetura planejada

1. A pergunta e o identificador do paciente são validados.
2. O LangGraph coordena a consulta ao prontuário e aos exames.
3. O LangChain recupera os protocolos relacionados à pergunta.
4. A LLM ajustada produz uma resposta contextualizada.
5. Uma camada de segurança valida a resposta.
6. O sistema retorna a orientação, as fontes e a necessidade de revisão humana.
7. As etapas são registradas em logs de auditoria.

## Estrutura do projeto

```text
app/                 Aplicação principal do assistente
  chains/            Pipelines e componentes LangChain
  graph/             Estados, nós e rotas do LangGraph
  database/          Consulta à base estruturada de pacientes
  safety/            Limites de atuação e validação das respostas
  observability/     Logs e trilha de auditoria
data/
  raw/               Dados originais antes do processamento
  processed/         Dataset anonimizado e preparado
  synthetic/         Prontuários e exames totalmente fictícios
  protocols/         Protocolos hospitalares fictícios
fine_tuning/         Preparação, treinamento e avaliação da LLM
notebooks/           Notebook executável no Google Colab
tests/               Testes automatizados
docs/                Relatório, diagramas e roteiro do vídeo
```

## Status

Projeto em desenvolvimento.

### Dados disponíveis

- cinco prontuários completamente sintéticos;
- cenários de rotina, revisão clínica, alerta e dados ausentes;
- protocolo fictício de acompanhamento de hipertensão;
- política de segurança e limites de atuação;
- dez perguntas e respostas internas para o pipeline de fine-tuning;
- validação automática da estrutura e de padrões comuns de dados pessoais.

## Próximas etapas

- [x] Criar dados clínicos sintéticos e protocolos internos.
- [ ] Implementar preprocessing e anonimização.
- [ ] Preparar o dataset de instruções.
- [ ] Executar fine-tuning com LoRA/QLoRA no Google Colab.
- [ ] Construir o pipeline com LangChain.
- [ ] Implementar o fluxo de decisão com LangGraph.
- [ ] Adicionar segurança, fontes, logs e testes.
- [ ] Criar a interface de demonstração.
- [ ] Documentar a avaliação e os resultados.
