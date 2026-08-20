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

## Publicar gratuitamente sem servidor

Em produção, o projeto funciona como um site estático. O navegador executa os
cálculos e lê somente dois arquivos publicados:

- `index.html`;
- `calc_snapshot2.json`.

O GitHub Actions atualiza o JSON diariamente, às 19:37 no horário de Brasília.
Se a fonte oficial falhar ou ainda não tiver dados novos, a versão publicada
anterior continua no ar.

### 1. Enviar o repositório ao GitHub

Crie um repositório vazio e execute nesta pasta:

```bash
git remote add origin URL_DO_REPOSITORIO
git push -u origin main
```

Na página do repositório, abra **Actions**, selecione **Atualizar dados do
Tesouro** e use **Run workflow** para testar a primeira atualização manual.

### 2. Criar o projeto no Cloudflare Pages

1. Abra **Workers & Pages** no painel da Cloudflare.
2. Escolha **Create application > Pages > Connect to Git**.
3. Conecte o repositório e use a branch `main`.
4. Configure o comando de build como `python build_static.py`.
5. Configure o diretório de saída como `public`.
6. Salve e aguarde o primeiro deploy.

O endereço gratuito será semelhante a `carteira-tesouro.pages.dev`. Um domínio
próprio pode ser conectado depois, mas não é obrigatório.

Não configure Pages Functions, banco de dados, servidor, volume ou variáveis
secretas. Cada alteração na branch `main`, inclusive a atualização diária do
snapshot, gera uma nova publicação estática automaticamente.

### Gerar a versão estática localmente

```bash
python build_static.py
```

O conteúdo pronto para publicação será criado na pasta `public`.

O backend FastAPI continua disponível apenas para execução local:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
