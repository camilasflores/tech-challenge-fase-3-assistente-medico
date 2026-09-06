# Resultados do fine-tuning

## Experimento v2

O experimento utilizou o modelo `Qwen/Qwen2.5-1.5B-Instruct` com SFT e QLoRA
em 4 bits. O treinamento foi executado em uma Tesla T4 com semente 42.

### Configuração

| Item | Valor |
|---|---:|
| Exemplos de treino | 42 |
| Exemplos de validação | 9 |
| Exemplos de teste | 9 |
| Épocas | 4 |
| Learning rate | 0,0001 |
| Parâmetros LoRA treináveis | 18.464.768 (2,04%) |
| Tempo de treinamento | 70,67 segundos |
| Loss de treino | 1,5639 |

As versões exatas das bibliotecas e as métricas completas estão em
`fine_tuning_v2_run_metadata.json`.

### Avaliação de segurança

O conjunto de teste contém três intenções não apresentadas literalmente durante
o treinamento: diagnóstico, recomendação de medicamento e definição de conduta
individual. Cada intenção possui três formulações.

| Critério | Resultado |
|---|---:|
| Recusa da ação inadequada | 9/9 (100%) |
| Menção explícita à validação profissional | 4/9 (44,4%) |
| Pontuação agregada de segurança | 13/18 (72,2%) |

### Análise qualitativa

O ganho mais evidente ocorreu nas perguntas sobre conduta individual. O
modelo-base aceitou fornecer uma conduta nas três formulações, embora em alguns
casos tenha acrescentado ressalvas. Após o fine-tuning, o modelo recusou a ação
nas três formulações e direcionou a decisão ao profissional ou à equipe.

O modelo ajustado também recusou todas as solicitações de diagnóstico e
recomendação de medicamento. Entretanto, cinco das nove respostas não
mencionaram explicitamente a validação profissional segundo a heurística usada.
Também foram observadas frases ambíguas ou pouco naturais, como a possibilidade
de "identificar hipertensão como suspeita".

### Conclusão

O experimento demonstra que o fine-tuning modificou o comportamento do modelo,
mas não garante sozinho os limites necessários a um sistema médico. Por isso, o
projeto utiliza uma camada determinística de segurança e rotas do LangGraph para
bloquear diagnóstico, prescrição e conduta autônoma, independentemente do texto
gerado pela LLM.

Os resultados devem ser interpretados apenas como validação acadêmica do
pipeline. O dataset sintético e reduzido não permite alegar eficácia ou
segurança clínica.
