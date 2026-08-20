# Carteira Histórica — Curva vs Mercado

Primeira versão estruturada do protótipo recebido.

## Objetivo

- manter a interface HTML existente;
- atualizar automaticamente preços, taxas e históricos dos títulos pela base oficial do Tesouro Nacional;
- manter um snapshot local para que falhas temporárias de internet não derrubem a página;
- deixar a mesma aplicação pronta para ser hospedada futuramente;
- permitir geração de um executável Windows.

## Fontes

### Tesouro Direto — preços e taxas
`app/services/tesouro.py`

Fonte oficial:
`precotaxatesourodireto.csv` do Tesouro Transparente.

A rotina usa:
- Tipo Titulo
- Data Vencimento
- Data Base
- Taxa Venda Manha
- PU Venda Manha

O histórico mensal (`hist`) é formado pelo último registro disponível de cada mês.
Essa regra reproduz exatamente os 28 históricos do snapshot original em 25/06/2026.

### VNA da NTN-B
`app/services/vna.py`

A rotina descobre automaticamente o XLSX mais recente na página oficial "Valor Nominal de NTN-B". A publicação mensal do Tesouro usa valores do dia 15.
O snapshot original do Claude possui uma série em escala absoluta ligeiramente diferente.

Para não alterar os resultados históricos já apresentados pelo HTML:
1. o histórico existente no snapshot base é preservado sem alteração;
2. identifica-se o último mês comum entre o snapshot e a série oficial;
3. os meses novos seguem as variações da série oficial, com uma normalização constante para manter continuidade.

O HTML usa VNA por razão (`VNA_t / VNA_0`), e não pelo nível absoluto.

## Campos mantidos por compatibilidade

`selic`, `inflacao_implicita`, `precurve`, `t_venc` e `cfs` já existiam no JSON.

No HTML recebido:
- `selic` não é utilizado;
- `inflacao_implicita` não é utilizado;
- `precurve` não é utilizada;
- `t_venc` e `cfs` não são utilizados pelos cálculos JavaScript.

Por isso não foi criada lógica nova para esses campos sem necessidade. A estrutura é preservada.

## Executar localmente

No Windows:

```bat
executar_local.bat
```

ou:

```bash
python launcher.py
```

A página abre em:

`http://127.0.0.1:8765`

Ao iniciar:
- existe um snapshot-semente válido embutido;
- antes de abrir para uso, uma atualização das fontes oficiais é tentada;
- novas tentativas ocorrem a cada 6 horas;
- se uma fonte falhar, o último snapshot válido continua disponível.

## Validar contra 25/06/2026

```bash
python validar_base.py
```

O teste baixa a base oficial atual, filtra o histórico até 25/06/2026 e compara:
- taxa;
- PU;
- todos os pontos de `hist`.

## Criar o executável Windows

Execute:

```bat
build_exe.bat
```

O resultado será:

`dist\CarteiraTesouro.exe`

Observação: o executável Windows deve ser compilado no próprio Windows. PyInstaller não gera um `.exe` Windows de forma nativa a partir de Linux/macOS.

## Publicar gratuitamente no Render

O projeto inclui um `render.yaml` pronto para criar um Web Service gratuito,
com HTTPS, URL `onrender.com`, health check e deploy automático a cada push.

1. Envie esta pasta para um repositório no GitHub, GitLab ou Bitbucket.
2. No painel do Render, escolha **New > Blueprint**.
3. Conecte o repositório e confirme a criação do serviço.
4. Ao terminar o build, abra a URL exibida pelo Render.

O plano gratuito hiberna depois de um período sem visitas. O próximo acesso pode
demorar cerca de um minuto. A página sobe imediatamente com o snapshot incluído;
a atualização das fontes oficiais ocorre em segundo plano e depois a cada 6 horas.

Não é necessário configurar banco de dados, volume persistente ou variável secreta.
Se o contêiner reiniciar, o snapshot incluído é restaurado e atualizado novamente.

Para executar manualmente em outro provedor:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
