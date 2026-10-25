# PEP 723（Inline script metadata）のツール対応状況

調査日: **2026-10-26（JST）**。

2026-03-21付のDeep Research「PythonのPEP 723（Inline Script Metadata）に関するツールサポート状況の網羅的調査」を、公式ドキュメント・リリースノート・issueで再調査した。元の[ChatGPT会話](https://chatgpt.com/c/69bdfec7-c18c-83a2-9f3a-befd4ad33042)は依頼文まで閲覧でき、結果本文はユーザー提供の貼り付けテキストで確認した。本書はその更新・補完版である。

## 結論と前回調査からの変更

**uv・pipx・Hatch・PDMの4つに加え、PEX・pip-run・ducktools-env・Pixi・marimoにも、PEP 723を利用した実行機能を確認できた。** 下の実行系の表は9ツール。ただしmarimoはノートブック用途であり、この9つが同じ機能を持つわけではない。さらにNox・toxのタスク／テスト環境、pipの依存導入、Renovateの依存更新、IDE・型検査、Nix用ライブラリにも用途が広がっている。根拠は各表・詳細節に示す。

「2024年の4ツールから5ツール増えた」とは数えない。PEX・Noxなどには2024年の実装があり、前回の調査対象から漏れていたものと、その後の新機能を区別する必要がある。

| 前回調査に対する変更 | 今回確認できた内容 | 時期・根拠 |
| --- | --- | --- |
| 新規対応 | toxに専用runnerを追加 | **4.52.0 / 2026-03-30**。[changelog](https://tox.wiki/en/4.65.4/changelog.html#v4-52-0-2026-03-30) |
| 新規対応 | Pixiが単独スクリプトの実行・依存編集・ロックに対応 | **0.76.0 / 2026-08-03**。[changelog](https://pixi.prefix.dev/latest/CHANGELOG/) |
| 既存対応の拡張 | pipxがPEP 723スクリプトの永続インストールに対応 | **1.16.0 / 2026-07-15**。[changelog](https://pipx.pypa.io/latest/changelog.html) |
| 実験的連携 | tyがuvでスクリプトごとの環境を用意し、型検査・補完等に利用 | **2026-10-13発表**。uv ≥0.12.3、ty ≥0.0.76。[公式発表](https://astral.sh/blog/uv-ty-integration) |
| 前回未掲載の補完 | PEXは実行とPEX生成、Noxはメタデータ読取に既に対応していた | PEX **2.6.0 / 2024-06-24**、Nox **2024.04.15**。[PEXリリース](https://github.com/pex-tool/pex/releases/tag/v2.6.0)、[Nox changelog](https://nox.thea.codes/en/stable/CHANGELOG.html) |
| 前回未掲載の補完 | marimo、pip-run、ducktools-env、Renovate、Pyproject.nix等 | 今回対応を確認。初出を確定できていないものは、新規対応の件数に含めない |
| 前回未掲載の補完 | PyCharmのuv環境でのスクリプト実行 | **2025.3.2**のリリースノートに掲載。[公式リリースノート](https://youtrack.jetbrains.com/articles/PY-A-233538505/PyCharm-2025.3.2-253.30387.127-build-Release-Notes) |

## 何を「対応」とするか

PEP 723は**メタデータの形式**を定める。Python本体に自動インストール機能を追加するものではなく、実行器・ロック形式・環境の保存先も共通化していない。`python script.py` だけでは、コメントから依存パッケージを導入しない。

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13"]
# ///

from rich import print

print("Hello, PEP 723!")
```

`script` ブロックのTOMLに `dependencies`、`requires-python`、`[tool]` を記述できる。現在の仕様では前2項目も省略可能。ツール固有の `[tool.uv]` 等が別ツールでも解釈されるとは限らない。最新仕様の確認先は[PyPAのInline script metadata仕様](https://packaging.python.org/en/latest/specifications/inline-script-metadata/)。[PEP 723](https://peps.python.org/pep-0723/)は現在Finalで、Resolutionは2024-01-08。これを各ツールの実装完了日と同一視しない。

本書では、**実行・ビルド／依存導入／更新／解析・IDE／パーサ**を分ける。「対応済み」は、その用途での公開機能を確認したという意味で、仕様全体の適合試験に合格したという意味ではない。

## 実行・配布に使えるツール

コマンドは上記の内容を `script.py` に保存した場合の例。各ツールをインストール済みとする。marimoの例はmarimo形式のノートブックに対して使う。

| ツール | 状況・用途 | 入口 | 確認した機能・制約 | 一次情報 |
| --- | --- | --- | --- | --- |
| uv | 対応済み／汎用実行 | `uv run script.py` | 依存環境・Python選択、依存編集、ロック・export・tree | [スクリプトガイド](https://docs.astral.sh/uv/guides/scripts/) |
| pipx | 対応済み／実行・アプリ導入 | `pipx run ./script.py` | 依存別の環境をキャッシュ。現在は `pipx install ./script.py` も提供 | [実行](https://pipx.pypa.io/latest/how-to/run-scripts.html)、[CLI](https://pipx.pypa.io/stable/reference/cli.html) |
| Hatch | 対応済み／汎用実行 | `hatch run script.py` | 必要な依存とPythonを備えた専用環境を作成。`[tool.hatch]` も利用可 | [スクリプト実行](https://hatch.pypa.io/latest/how-to/run/python-scripts/) |
| PDM | 対応済み／汎用実行 | `pdm run script.py` | 一時環境に依存を導入。`--reuse-env` と `[tool.pdm]` に対応 | [Single-file Scripts](https://pdm-project.org/latest/usage/scripts/#single-file-scripts) |
| PEX | 対応済み／実行・配布物生成 | `pex --exe script.py` | 依存とPython要件を読み取る。`--output app.pex` でPEXを生成 | [2.6.0リリース](https://github.com/pex-tool/pex/releases/tag/v2.6.0) |
| pip-run | 対応済み／依存付き実行 | `pip-run script.py` | `dependencies` を読み取り、一時的なインストール先を用意。既存の `__requires__` 形式も併存 | [Script-declared Dependencies](https://github.com/jaraco/pip-run#script-declared-dependencies) |
| ducktools-env | 対応済み／実行・zipapp化 | `ducktools-env run script.py` | `bundle` で環境作成用ツールを含むzipappを生成。Python要件、スクリプト登録、独自ロックも提供 | [公式README](https://github.com/DavidCEllis/ducktools-env) |
| Pixi | 対応済み／汎用実行 | `pixi run --script script.py` | Python・PyPI依存に加え、`[tool.pixi]` でConda依存を扱える。依存編集・ロックにも対応 | [Standalone Scripts](https://pixi.prefix.dev/latest/python/scripts/) |
| marimo | 対応済み／ノートブック編集・実行 | `uvx marimo edit --sandbox notebook.py` | ノートブック内に要件を保存。uvまたはPixiでノートブックごとの環境を作成 | [Package management](https://docs.marimo.io/guides/package_management/) |

pip-runについては、ここでは依存宣言を使った実行を確認している。上表だけから `requires-python` に応じた別Pythonの自動取得まで対応しているとは判断しない。

### uv: 既存4ツールの中でも運用機能が多い

実行対応の初出は **0.2.19**。[0.2系changelog](https://github.com/astral-sh/uv/blob/main/changelogs/0.2.x.md)で確認できる。スクリプトのロックは **0.5.17**で追加された。[0.5系changelog](https://github.com/astral-sh/uv/blob/main/changelogs/0.5.x.md)

```sh
uv init --script script.py --python 3.11
uv add --script script.py rich
uv run script.py
uv lock --script script.py
uv run --locked script.py
```

`uv init` は新規スクリプトを作る例。ロックすると隣に `script.py.lock` ができる。ロックがあっても通常の実行では必要に応じて更新されるため、変更を検知して止めたい場合は `--locked` を使う。`[tool.uv].exclude-newer` で候補の公開日時も制限できる。[公式ガイド](https://docs.astral.sh/uv/guides/scripts/#locking-dependencies)

なお、ファイル実行と `uv run -m module` は同じではない。モジュール実行時のinline metadata解釈を求める [#8317](https://github.com/astral-sh/uv/issues/8317) は調査時点でOpen、`needs-decision`。

### pipx・Hatch・PDM: 初出と現在の機能を分ける

- **pipx**: 1.3.0で暫定仕様のinline metadataに対応し、**1.4.2**で現在の `/// script` とトップレベルの依存宣言に追随。現在のドキュメントは `requires-python` の適合確認も明記している。古いpipxについて同じ挙動とは断定しない。[changelog](https://pipx.pypa.io/latest/changelog.html)、[現在の実行仕様](https://pipx.pypa.io/latest/how-to/run-scripts.html)
- **Hatch**: **1.10.0 / 2024-05-02**でスクリプト実行を追加。現在はスクリプトのインストーラとしてuvが既定で、`[tool.hatch]` から設定できる。[履歴](https://hatch.pypa.io/latest/history/hatch/#1100-2024-05-02)、[現在の仕様](https://hatch.pypa.io/latest/how-to/run/python-scripts/)
- **PDM**: **2.16.0**で追加。毎回の一時環境作成と `--reuse-env` による再利用を選べる。[公式ガイド](https://pdm-project.org/latest/usage/scripts/#single-file-scripts)

前回の「pipxは実行中心」という説明には、現在の永続インストール機能を補う必要がある。一方、ツールのプロジェクト用ロック機能が、そのままPEP 723スクリプト用ロックにも使えるとは限らない。

### marimo: PEP 723をノートブックの環境情報として使う

marimoは `.py` 形式のノートブックに、Python要件と依存パッケージを埋め込む。sandboxモードではノートブックごとの環境を用意し、エディタでパッケージを追加すると環境とメタデータの両方を更新する。周囲のプロジェクト環境の依存は引き継がない。[公式ガイド](https://docs.marimo.io/guides/package_management/#working-in-a-sandbox)

```sh
# uvを利用するノートブック環境
uvx marimo edit --sandbox notebook.py

# Pixiを利用するノートブック環境
pixi exec marimo edit --sandbox=pixi notebook.py
```

`uvx`／`pixi exec` はmarimo自体を起動し、`--sandbox` はノートブック用の別環境を用意する指定。現在のガイドには両バックエンドが掲載されている。これはパッケージの隔離であり、OSレベルの権限制限ではない。また、marimoのこの機能があることからJupyter全体の対応まで推定しない。

### Pixiとducktools-env: 配布・再現性の選択肢

Pixi **0.76.0**は `--script` を用いた実行・初期化・依存編集・ロック等を追加した。**0.79.0**では実行せず環境だけ導入する `pixi install --script` も追加。通常の `dependencies` と `requires-python` は共通形式で、Conda側の依存は `[tool.pixi]` の拡張として記載する。[公式changelog](https://pixi.prefix.dev/latest/CHANGELOG/)、[スクリプトガイド](https://pixi.prefix.dev/latest/python/scripts/)

ducktools-envは `bundle` でzipapp化できる。利用者には起動用のPythonが必要だが、専用runnerの事前インストールを省ける。ロック生成にはuvを利用し、独自の `script.py.dtenv.lock` を使う。uvの `script.py.lock` と取り違えない。[公式READMEのLocking environments](https://github.com/DavidCEllis/ducktools-env#locking-environments)

## タスク・テスト環境

| ツール | 状況 | 対応内容・入口 | 一次情報 |
| --- | --- | --- | --- |
| Nox | 対応済み | **2024.04.15**で `nox.project.load_toml()` による読取。**2025.02.09**でnoxfile自身のPEP 723依存にも対応。現在は `session.install_and_run_script()` も掲載 | [changelog](https://nox.thea.codes/en/stable/CHANGELOG.html)、[チュートリアル](https://nox.thea.codes/en/stable/tutorial.html#loading-dependencies-from-pyproject-toml-or-scripts) |
| tox | 対応済み | **4.52.0**から `virtualenv-pep-723` runner。`script` で対象を指定し、依存とPython要件を読取 | [使い方](https://tox.wiki/en/stable/how-to/usage.html#run-a-pep-723-script)、[仕様](https://tox.wiki/en/latest/user_guide.html#inline-script-metadata-pep-723) |

toxの例（`tox.toml`）:

```toml
[env.example]
runner = "virtualenv-pep-723"
script = "script.py"
```

`tox r -e example` で実行する。このrunnerでは `deps` や `base_python` の重複指定を避ける設計になっている。Pythonは通常の探索で決め、`requires-python` への適合を検証する。uvのように任意のPythonを自動取得することまで、このrunnerの対応から推定しない。

Noxは汎用runnerとしての9ツールには数えていない。既存のセッションからスクリプトの依存を読む機能と、noxfile自身の依存を宣言する機能を持つ。

## 依存導入・自動更新・検査・パーサ

| ツール／ライブラリ | 状況 | できること・制約 | 一次情報 |
| --- | --- | --- | --- |
| pip | 対応済み／依存導入の入力 | **26.0**で `--requirements-from-script`。スクリプト実行や専用venv作成は行わない | [CLI](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-requirements-from-script)、[26.0履歴](https://pip.pypa.io/en/stable/news/#v26-0) |
| Renovate | 対応済み／依存更新 | `pep723` managerでPyPI依存を更新。**既定では対象ファイルを検出しないため設定が必要** | [manager仕様](https://docs.renovatebot.com/modules/manager/pep723/) |
| Dependabot | 要望あり／未対応 | [#11946](https://github.com/dependabot/dependabot-core/issues/11946) はOpen、マイルストーンなし。uv.lock対応と別件 | [公式issue](https://github.com/dependabot/dependabot-core/issues/11946) |
| pip-tools | 要望あり／リリース済み対応を確認できず | [#2027](https://github.com/jazzband/pip-tools/issues/2027) はOpen、`PR wanted`。実装提案 [#2107](https://github.com/jazzband/pip-tools/pull/2107) が関連 | [公式issue](https://github.com/jazzband/pip-tools/issues/2027) |
| pytest-pep723 | 対応済み／追加プラグイン | スクリプトのimportに必要な依存宣言が揃っているか検査。pytest本体のPEP 723対応とは区別 | [公式ドキュメント](https://pytest-pep723.rgoswami.me/) |
| Pyproject.nix | 対応済み／Nix用ライブラリ | `lib.scripts.loadScript` で読取、`renderWithPackages` でNixのPythonを指すshebangを生成 | [scripts API](https://pyproject-nix.github.io/pyproject.nix/lib/scripts.html) |
| ducktools-scriptmetadata | 対応済み／パーサ | スクリプトメタデータの解析用。単独での依存導入・実行とは別 | [公式リポジトリ](https://github.com/DavidCEllis/ducktools-scriptmetadata) |
| python-script-runner | 対応runnerへの委譲 | 共通shebang用のラッパー。uv・pipx・Hatch・pip-runを探索して起動。独自の依存解決器とは数えない | [公式README](https://github.com/dbohdan/python-script-runner) |

pipの利用例:

```sh
python -m venv .venv
.venv/bin/python -m pip install --upgrade 'pip>=26.0'
.venv/bin/python -m pip install --requirements-from-script script.py
.venv/bin/python script.py
```

上記はmacOS/Linux用。Windowsでは `.venv\Scripts\python.exe` に読み替える。pipが解決するのは依存パッケージであり、この操作自体がスクリプト用Pythonを選択してくれるわけではない。26.0のchangelog日付は **2026-01-30**、[リリース告知](https://discuss.python.org/t/announcement-pip-26-0-release/105947)は **2026-01-31**であり、区別して扱う。

Renovateの設定例（`renovate.json`、対象ディレクトリを絞る）:

```json
{
  "pep723": {
    "managerFilePatterns": ["/^scripts/.*\\.py$/"]
  }
}
```

この例は `scripts/` 以下を指定する。実際の配置に合わせて変更すること。抽出した依存の更新対応と、各runner固有のロックファイルを再生成できるかは別に確認する。

## IDE・型検査・lint

| ツール | 判定 | 現状と追跡先 |
| --- | --- | --- |
| ty + uv | **実験的対応** | スクリプトごとにuvで環境を用意し、CLIの型検査とLSPの補完・定義ジャンプ等に利用。[2026-10-13公式発表](https://astral.sh/blog/uv-ty-integration)、[設定仕様](https://docs.astral.sh/ty/reference/editor-settings/#experimentaluseuv) |
| PyCharm | **uv経由の実行に対応** | [PY-79638](https://youtrack.jetbrains.com/issue/PY-79638) はFixed、Available inは2025.3.2。[同版リリースノート](https://youtrack.jetbrains.com/articles/PY-A-233538505/PyCharm-2025.3.2-253.30387.127-build-Release-Notes)にも掲載。全runnerへの対応とは解釈しない |
| VS Code Python／Python Environments | **開発中・一部機能あり** | 元の [vscode-python #24916](https://github.com/microsoft/vscode-python/issues/24916) はOpen。現在の具体的な実装計画は [vscode-python-environments #1602](https://github.com/microsoft/vscode-python-environments/issues/1602)。環境管理・ファイル別連携が進んでいるが、CodeLensと一括セットアップは未完了のチェック項目。一般提供済みと断定しない |
| Pylance | **環境連携・宣言編集の機能あり** | 現在の[公式説明](https://github.com/microsoft/pylance-release/blob/main/docs/howto/dependency-management.md)には、Python Environmentsが選んだファイル別インタプリタの利用と、単独 `.py` ファイルへのPEP 723依存ブロック生成・更新を掲載。自動依存導入とは別。main上の説明であり、各機能の初出安定版は今回特定できず |
| Ruff | **設定読取は要望段階** | [#10457](https://github.com/astral-sh/ruff/issues/10457) はOpen。PEP内での賛同表明や、コメント誤検出への対策は、`[tool.ruff]`／`requires-python` の設定対応と同義ではない |
| mypy | **直接対応を確認できず** | [設定ファイル](https://mypy.readthedocs.io/en/stable/config_file.html)と[inline設定](https://mypy.readthedocs.io/en/stable/inline_config.html)は別方式。`# mypy:` コメントの対応をPEP 723対応と数えない。リリース済みのブロック読取・環境自動選択は今回確認できず |

tyの最低要件は **uv 0.12.3 / ty 0.0.76**。スクリプト連携を有効にする例:

```sh
TY_UV=scripts ty check script.py
```

VS Codeのty拡張では次の設定を利用する:

```json
{
  "ty.experimental.useUv": "scripts"
}
```

自動環境作成はopt-inで、未信頼ワークスペースでは無効。公式発表には将来の既定有効化と `uv check` のRuff連携予定もあるが、調査時点では将来計画である。[公式発表](https://astral.sh/blog/uv-ty-integration)、[エディタ設定](https://docs.astral.sh/ty/reference/editor-settings/#experimentaluseuv)

Pylanceについては、従来の検索結果に「PEP 723をimport解決の入力にしない」とする記述があるが、調査時点の公式ドキュメント本文にはファイル別環境の利用が記載されている。依存宣言を読んで自らパッケージを導入すること、別拡張が用意した環境で解析すること、宣言を書き出すことを分けて追う。

注意: tyの[Typing FAQ](https://docs.astral.sh/ty/reference/typing-faq/)には、複数スクリプトの個別依存をまだ認識しないという従来の説明が残っている。一方、新しい公式発表・エディタ設定には実験的連携が明記される。本書では**実験設定を有効にした場合の対応**として整理し、既定で対応済みとは記載しない。

## 未確認・対象範囲の注意

「未確認」は非対応の証明ではない。対応機能の根拠が得られたものと、周辺ツールを組み合わせれば実現できるものを区別する。

| 対象 | 今回の整理 | 確認先・補足 |
| --- | --- | --- |
| Poetry | 本体のPEP 723スクリプト読取・環境作成・実行機能は確認できず | [公式CLI](https://python-poetry.org/docs/cli/)、[公式issue検索](https://github.com/python-poetry/poetry/issues?q=%22PEP+723%22)。具体的な提供予定も特定できず |
| Pipenv | 本体の専用対応は確認できず | [公式ドキュメント](https://pipenv.pypa.io/en/latest/)、[公式issue検索](https://github.com/pypa/pipenv/issues?q=%22PEP+723%22)。pip側の対応だけではPipenvの対応を意味しない |
| Rye | 非対応と公式に明記 | [uv移行ガイド](https://rye.astral.sh/guide/uv/)が `uv init --script` をRyeにない機能として説明 |
| Pants | PEP本文に賛同はあるが、今回リリース済みの直接対応を確認できず | [PEPのTooling buy-in](https://peps.python.org/pep-0723/#tooling-buy-in)。PEXの実装をそのままPants本体の対応と数えない |
| venv／virtualenv | 環境作成機能とPEP 723の解釈は別 | [venv](https://docs.python.org/3/library/venv.html)、[virtualenv](https://virtualenv.pypa.io/en/latest/)。tox等が上位でメタデータを読むことは、これら単体の専用対応を意味しない |
| flit／build／setuptools | 単独スクリプトrunnerとしての対応は確認できず | [flit](https://flit.pypa.io/en/stable/)、[build](https://build.pypa.io/en/stable/)、[setuptools](https://setuptools.pypa.io/en/latest/)。パッケージのビルド機能をPEP 723実行対応と混同しない |
| Conda／Mamba | 本体の専用対応は確認できず | [Conda](https://docs.conda.io/projects/conda/en/stable/)、[Mamba](https://mamba.readthedocs.io/en/latest/)。Condaエコシステムには上記Pixiの実装がある |
| Nix／Homebrew | 本体・エコシステムを一括で未対応とはしない | Nix周辺には上記Pyproject.nixの実装がある。[Homebrew](https://docs.brew.sh/)でuv等をインストールできることと、Homebrew自身によるメタデータ読取は別 |

## 次回更新時の確認項目

1. tox・Pixi・ty等の初出版と、現行版の挙動を分けて追う。`latest` ドキュメントやmain上のコードだけから、安定版での提供を断定しない。
2. Dependabot #11946、pip-tools #2027、Ruff #10457、VS Code Environments #1602の状態と、リリースノートを照合する。issueがClosedというだけで実装済みとしない。
3. marimoのuv／Pixiバックエンド、ノートブックへのメタデータ書き戻し、独立環境の扱いを再確認する。
4. `[tool.*]` の可搬性、`requires-python` の適合確認・Python取得、ロック形式をツールごとに確認する。

本調査は公開一次資料とissueの照合によるもの。全ツールのインストール・実行試験やPEPの全規則への適合試験は行っていない。初出を確定できなかったツールには推測の日付を付けていない。
