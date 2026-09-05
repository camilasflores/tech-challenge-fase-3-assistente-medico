# Dados do projeto

Todos os registros deste diretório são fictícios e foram criados apenas para
fins acadêmicos. Eles não representam pessoas, atendimentos ou orientações de
um hospital real.

## Separação por finalidade

| Diretório | Conteúdo | Uso |
|---|---|---|
| `raw/` | FAQs antes do processamento | Entrada do pipeline de fine-tuning |
| `processed/` | Dados limpos e anonimizados | Treinamento e avaliação |
| `synthetic/` | Pacientes, sinais vitais e exames fictícios | Consulta estruturada em tempo de execução |
| `protocols/` | Protocolos internos fictícios | Recuperação de contexto e fontes |

Os prontuários não fazem parte do fine-tuning. Essa separação permite atualizar
os dados do paciente sem treinar novamente a LLM e reduz o risco de memorização
de informações pessoais.

## Cenários cobertos

- acompanhamento estável;
- pressão arterial repetidamente elevada;
- exames de acompanhamento pendentes;
- sintomas que exigem avaliação imediata;
- prontuário incompleto.

## Validação

Execute na raiz do projeto:

```bash
python -m fine_tuning.validate_data
python -m fine_tuning.prepare_dataset
```

O comando verifica a estrutura dos pacientes, IDs duplicados e presença de
informações pessoais proibidas nos dados sintéticos.

O segundo comando normaliza e anonimiza as FAQs, cria três formulações de cada
pergunta e gera `train.jsonl`, `validation.jsonl`, `test.jsonl` e
`quality_report.json`. A divisão é realizada pelo ID da FAQ original, portanto
variações da mesma pergunta nunca aparecem em conjuntos diferentes.
