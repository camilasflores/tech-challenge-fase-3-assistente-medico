# Decisões de arquitetura

## Escopo clínico

O protótipo será limitado ao acompanhamento de pacientes adultos com
hipertensão. A limitação reduz ambiguidades e permite criar protocolos, exames,
perguntas e regras de segurança coerentes entre si.

## Separação dos dados

- **Dataset de fine-tuning:** ensina formato, linguagem e limites de resposta.
- **Protocolos internos:** recuperados em tempo de execução para fornecer fontes.
- **Prontuários sintéticos:** consultados em tempo de execução para representar
  informações atualizadas do paciente.

Prontuários não serão incorporados ao treinamento do modelo, pois podem mudar e
devem permanecer separados dos parâmetros da LLM.

## Segurança

O sistema será um apoio à decisão, não um substituto do profissional. Respostas
com prescrição direta, alteração de dose ou diagnóstico definitivo serão
bloqueadas ou encaminhadas para validação humana.

## Privacidade

Todos os pacientes e registros clínicos do protótipo serão fictícios. Nenhum
dado pessoal real será armazenado no repositório.
