# Roteiro do vídeo - duração estimada de 12 a 14 minutos

## 1. Abertura e problema - 1 minuto

- Apresentar o Tech Challenge e o objetivo do assistente.
- Explicar que o escopo foi limitado ao acompanhamento de hipertensão em
  adultos e que todos os dados são sintéticos.
- Destacar que o sistema apoia a equipe, mas não diagnostica nem prescreve.

## 2. Dados e fine-tuning - 3 minutos

- Mostrar `data/raw`, `data/synthetic`, `data/protocols` e `data/processed`.
- Explicar preprocessing, anonimização, curadoria e divisão 42/9/9.
- Abrir o notebook e mostrar as células de QLoRA, sem executar o treinamento.
- Explicar que QLoRA quantiza o Qwen em 4 bits e treina adaptadores LoRA.
- Mostrar os resultados: quatro épocas, 70,67 segundos, loss 1,5639 e 2,04% de
  parâmetros treináveis.
- Mostrar que 9/9 pedidos inadequados foram recusados e explicar a limitação da
  menção à validação humana em 4/9 respostas.

## 3. Arquitetura - 3 minutos

- Mostrar o diagrama do relatório.
- SQLite: dados estruturados e atualizados dos pacientes.
- LangChain: ferramentas, divisão dos protocolos, embeddings e recuperação dos
  trechos mais relevantes.
- LangGraph: estado, nós, decisões e rotas determinísticas.
- Qwen + LoRA: geração somente no fluxo comum.
- Validador: rejeição de comando clínico, fato alterado ou regra inventada.
- Auditoria: metadados e fontes, sem armazenar texto clínico livre.

## 4. Demonstração na interface - 4 a 5 minutos

1. `PAC-001`, pergunta `Quais exames estão pendentes?`
   - Mostrar resposta da LLM, fontes, nós e ausência de fallback.
2. `PAC-003`, mesma pergunta.
   - Mostrar, se ocorrer, o fallback protegendo os nomes dos exames.
3. `PAC-004`, pergunta `Qual é a situação atual do paciente?`
   - Mostrar a rota de revisão imediata e explicar por que a LLM não é acionada.
4. `PAC-005`, mesma pergunta.
   - Mostrar os campos ausentes e a ausência de dados inventados.
5. Pergunta `Qual medicamento devo prescrever para este paciente?`
   - Mostrar o bloqueio antes da consulta ao prontuário.

Abrir “Fontes e rastreabilidade” em pelo menos um cenário e mostrar o `run_id`,
as fontes e os nós percorridos.

## 5. Resultados e encerramento - 1 a 2 minutos

- Mostrar `docs/results` e informar que a suíte possui 43 testes aprovados.
- Ressaltar que o fine-tuning mudou o comportamento, mas não é usado como única
  barreira de segurança.
- Apresentar as limitações: dataset sintético e pequeno, escopo restrito e
  ausência de validação clínica real.
- Encerrar reforçando que o projeto é acadêmico e exige validação humana.

## Frase de encerramento sugerida

“O projeto demonstra que uma LLM personalizada pode apoiar a organização de
informações clínicas, desde que seja cercada por dados rastreáveis, decisões
determinísticas, validação independente e supervisão humana.”

