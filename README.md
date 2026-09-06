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
- vinte perguntas e respostas internas para o pipeline de fine-tuning;
- validação automática da estrutura e de padrões comuns de dados pessoais.

## Fine-tuning no Google Colab

O notebook [`notebooks/01_fine_tuning_qlora.ipynb`](notebooks/01_fine_tuning_qlora.ipynb)
executa SFT com QLoRA sobre o modelo `Qwen/Qwen2.5-1.5B-Instruct`. Ele inclui:

- verificação da GPU;
- carregamento dos conjuntos de treino, validação e teste;
- quantização do modelo-base em 4 bits;
- configuração dos adaptadores LoRA;
- captura de respostas antes e depois do treinamento;
- curva de perda, metadados da execução e exportação do adaptador.

Os resultados reais da execução v2 e sua análise estão documentados em
[`docs/results/`](docs/results/).

## Base estruturada de prontuários

Os prontuários sintéticos são carregados em SQLite para representar a consulta
a dados atualizados do paciente. O banco é reproduzível e não é versionado:

```bash
python -m app.database.seed
```

O módulo `PatientRepository` oferece consultas parametrizadas e somente leitura.
As ferramentas LangChain `get_patient_record` e `get_pending_exams` expõem
resultados estruturados e incluem a identificação da fonte consultada.

## Busca nos protocolos (RAG)

O módulo `protocol_retriever` divide os documentos Markdown em trechos e os
indexa com `InMemoryVectorStore`. Por padrão, utiliza o modelo multilíngue local
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, sem exigir uma
API paga. A ferramenta LangChain `search_internal_protocols` devolve o conteúdo
recuperado com identificador, título, caminho do arquivo e índice do trecho.

Na primeira execução, o modelo de embeddings é baixado pelo Hugging Face. A
indexação ocorre novamente quando a aplicação é iniciada, o que é adequado para
os dois protocolos pequenos desta demonstração.

## Fluxo de decisão com LangGraph

O `AssistantState` transporta pergunta, prontuário, prioridade, fontes e nós
executados. O grafo aplica as seguintes rotas determinísticas antes de qualquer
geração por LLM:

1. valida a pergunta e o identificador sintético;
2. bloqueia pedidos de diagnóstico, prescrição ou alteração de dose;
3. consulta o prontuário SQLite somente em pedidos permitidos;
4. interrompe o fluxo comum quando há sintomas de alerta registrados;
5. solicita os dados ausentes sem inventar conteúdo;
6. recupera os protocolos e compõe um resumo rastreável nos demais casos.

Para experimentar o fluxo após instalar as dependências:

```bash
python -m app.main PAC-003 "Quais exames estão pendentes?"
```

Na primeira execução, o modelo de embeddings será baixado. A saída JSON inclui
`priority`, `final_answer`, `sources`, `executed_nodes` e a indicação de revisão
humana obrigatória.

## Inferência com o adaptador LoRA

O fluxo aceita qualquer implementação do contrato `TextGenerator`. Quando a
variável `LORA_ADAPTER_PATH` aponta para o adaptador exportado pelo notebook, o
`HuggingFaceLoRAGenerator`:

1. lê o modelo-base de `adapter_config.json`;
2. carrega o tokenizer e o `Qwen2.5-1.5B-Instruct`;
3. aplica os pesos com `PeftModel.from_pretrained`;
4. formata as mensagens com o chat template do tokenizer;
5. gera a resposta de forma determinística.

No Colab, envie o ZIP para `/content` e execute estas células. O extrator copia
somente os arquivos necessários para inferência e ignora os checkpoints e o
estado do otimizador:

```python
!python -m app.models.adapter_archive "/content/assistente-medico-lora (2).zip" "/content/assistente-medico-lora"
%env LORA_ADAPTER_PATH=/content/assistente-medico-lora
!python -m app.main PAC-003 "Quais exames estão pendentes?"
```

Se o Colab apresentar conflito entre o PEFT e uma versão antiga do pacote
opcional TorchAO, remova-o com `!pip uninstall -y torchao` e reinicie somente a
sessão. O adaptador LoRA deste projeto não depende do TorchAO.

Sem essa variável, a aplicação usa um fallback seguro e continua executável.
Depois da geração, a resposta passa por uma verificação independente. Saídas
vazias, erros do modelo ou comandos clínicos diretos são substituídos por um
resumo determinístico. O log registra o modelo utilizado e se houve fallback,
mas nunca registra o texto gerado.

## Auditoria e privacidade

Todas as rotas terminam no nó `audit_execution`. Cada execução acrescenta um
evento ao arquivo local `artifacts/audit.jsonl` com:

- UUID da execução e horário UTC;
- identificador sintético validado;
- prioridade, bloqueio e necessidade de validação humana;
- nós percorridos, fontes consultadas e regras acionadas.

O log não armazena a pergunta, o prontuário completo nem a resposta final. O
diretório `artifacts/` está ignorado pelo Git e pode ser recriado localmente.
Para visualizar os últimos eventos:

```bash
tail -n 5 artifacts/audit.jsonl
```

## Interface de demonstração

A aplicação Streamlit reúne os cinco pacientes sintéticos, campo de pergunta,
prioridade, resposta, modelo acionado, fallback de segurança, fontes, nós do
LangGraph e identificador da auditoria. O prontuário completo e os trechos de
contexto não são exibidos na tela principal.

Com o ambiente e, opcionalmente, `LORA_ADAPTER_PATH` configurados:

```bash
python -m streamlit run streamlit_app.py
```

O grafo é mantido em cache durante a sessão da interface para evitar recarregar
embeddings e modelo a cada interação.

Para executar, abra o notebook pelo GitHub no Google Colab e selecione uma GPU
T4 em **Ambiente de execução → Alterar o tipo de ambiente de execução**.

## Próximas etapas

- [x] Criar dados clínicos sintéticos e protocolos internos.
- [x] Implementar preprocessing e anonimização.
- [x] Preparar o dataset de instruções.
- [x] Executar fine-tuning com LoRA/QLoRA no Google Colab.
- [x] Criar as ferramentas LangChain para prontuários e protocolos.
- [x] Integrar prontuários e protocolos no pipeline de resposta.
- [x] Implementar o fluxo de decisão com LangGraph.
- [x] Adicionar regras de segurança, fontes, logs e testes.
- [x] Integrar o carregador do modelo-base com o adaptador LoRA.
- [x] Validar a estrutura e a integridade dos pesos do adaptador real.
- [x] Validar a inferência com o adaptador LoRA real.
- [x] Adicionar grounding para nomes de exames e referências a regras.
- [x] Criar a interface de demonstração.
- [ ] Documentar a avaliação e os resultados.
