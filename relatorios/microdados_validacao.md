# Validação — microdados de vacinação (recorte CE)

- Partes: ['parte_part-00000-0656f017-a858-4d09-9c29-8eb772735eb9.c000.csv.gz', 'parte_part-00001-0656f017-a858-4d09-9c29-8eb772735eb9.c000.csv.gz', 'parte_part-00002-0656f017-a858-4d09-9c29-8eb772735eb9.c000.csv.gz', 'parte_part-00003-0656f017-a858-4d09-9c29-8eb772735eb9.c000.csv.gz', 'parte_part-00004-0656f017-a858-4d09-9c29-8eb772735eb9.c000.csv.gz']
- Excluídas: 2,184,834 de outras vacinas; 131,617 de Covid fora de 2021-01-17 a 2024-04-16
- Linhas mantidas (Covid, no período, residência ou aplicação no CE): 25,543,056
- Datas inválidas/ausentes: 0; período: dia 16 a 1201 desde 01/01/2021
- Linhas duplicadas removidas (podem vir de sobreposição entre arquivos): 101,160

## Mapeamento de vacina_descricao_dose (antes de remover duplicatas)

| dose                |       n | classe   |
|:--------------------|--------:|:---------|
| 1ª Dose             | 8413297 | D1       |
| 2ª Dose             | 7319899 | D2       |
| Reforço             | 6487691 | REF      |
| 2º Reforço          | 2277028 | REF      |
| 1º Reforço          |  326679 | REF      |
| Dose Adicional      |  242128 | REF      |
| Única               |  140205 | DU       |
| 3ª Dose             |  133513 | REF      |
| 3º Reforço          |  116569 | REF      |
| Dose                |   26284 | DU       |
| 2ª Dose Revacinação |   14809 | D2       |
| 1ª Dose Revacinação |   13636 | D1       |
| 4ª Dose Revacinação |   11590 | REF      |
| Revacinação         |    8542 | REF      |
| 3ª Dose Revacinação |    6500 | REF      |
| 5ª Dose             |    4457 | REF      |
| 4ª Dose             |     109 | REF      |
| 5ª Dose Revacinação |     102 | REF      |
| Dose Inicial        |       7 | REF      |
| (vazio)             |       4 | REF      |
| 1ª Dose Fracionada  |       3 | D1       |
| 2ª Dose Fracionada  |       2 | D2       |
| 4ª Dose Fracionada  |       1 | REF      |
| 3ª Dose Fracionada  |       1 | REF      |

- Municípios do CE com dados: 184 (residência), 184 (aplicação)
- Doses de residentes do CE aplicadas fora do CE: 0
- Doses aplicadas no CE em residentes de fora: 1,038,271
- Municípios > 100% (D1+DU, Censo): residência 60, aplicação 3
- Abandono individual (mediana): 0.143
