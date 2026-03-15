# Agentic RAG — 調査結果

リボルブ・シス向け RAG システムリプレイスの技術調査。
Pydantic AI を軸に、Azure / AWS 両環境での構成を検討する。

---

## 1. Pydantic AI — プロダクションレディネス

### 結論: Production Ready

| 項目 | 詳細 |
|------|------|
| 現バージョン | v1.68.0（2026-03-13） |
| GA リリース | v1.0.0（2025-09-04） |
| PyPI 分類 | `5 - Production/Stable` |
| GitHub Stars | 15,459 |
| Contributors | 387人 |
| リリース頻度 | 週1-2回 |
| ライセンス | MIT |
| Python 対応 | 3.10 - 3.14 |

**API 安定性コミット:**
> "we're committed to API stability: we will not introduce changes that break your code until V2."

**注意点:**
- Pydantic Graph（マルチエージェント）は Beta API
- v0.x → v1.0 で `result` → `output` のリネームあり（古い記事に注意）
- リリース頻度が高いので依存バージョンの固定を推奨

### 採用理由（lab/agentic-frameworks での比較を踏まえて）

| 理由 | 詳細 |
|------|------|
| LLM Agnostic | 20+ プロバイダー対応。Azure OpenAI も `AzureProvider` で公式サポート |
| 型安全 | Pydantic バリデーション + IDE フルサポート。ツール定義がデコレータ + 型ヒントだけで済む |
| Agent Architecture の簡素化 | MCP サーバー構築不要（Claude Agent SDK 比）、セッション管理不要（Google ADK 比） |
| Production/Stable | v1.0 GA。API 安定性コミットあり |

---

## 2. LLMOps / Observability

### LLMOps に必要な機能

LLM アプリの本番運用には以下の仕組みが必要:

- エージェント実行ごとのトレース（モデルリクエスト・ツールコール単位の span）
- トークン使用量・コスト・レイテンシの継続的モニタリング
- 検索精度・回答品質の定量評価
- プロンプト変更の影響測定

### 運用監視の選択肢

**クラウドネイティブな監視サービス** で運用メトリクスを取得し、必要に応じて **LLM 特化の Observability ツール** を併用する構成が現実的。

| カテゴリ | ツール | 概要 |
|---------|-------|------|
| クラウド監視（Azure） | Application Insights | メトリクス・ログ・ダッシュボード・アラート |
| クラウド監視（AWS） | CloudWatch + X-Ray | メトリクス・ログ・分散トレーシング |
| LLM 特化 Observability | Langfuse（OSS） | トレース・プロンプト管理・評価を一体化。セルフホスト可能 |
| LLM 特化 Observability | Langsmith | LangChain エコシステム向け。トレース・評価・データセット管理 |

**技術基盤:** いずれも OpenTelemetry ベース。Pydantic AI は OpenTelemetry に対応しているため、ツールの選択はフレームワークに縛られない。

**Langfuse** は LLM 固有のトレース可視化（ツールコールの検査、トークン消費量の追跡等）やプロンプトの A/B テストに対応しており、クラウド非依存で使える選択肢の一つ。

---

## 3. 検索エンジン

### ハイブリッド検索の重要性（共通）

クラウドに依らず、検索エンジンの選択で重要なのはハイブリッド検索のサポート。単一の検索方式では取りこぼしが生じる。

| 検索方式 | エンジン | 用途 |
|---------|--------|------|
| Full-Text / Keyword | BM25（転置インデックス） | 完全一致・部分一致。型番・固有名詞に強い |
| Vector | HNSW 等のベクトルインデックス | 埋め込みベクトルによる意味的類似検索 |
| Hybrid | BM25 + Vector → RRF 等で統合 | キーワードとベクトルの併用。精度最良 |
| Semantic Ranking | ML モデルによるリランキング | 上記いずれかの結果に対する再順位付け |

**推奨:** Hybrid 検索（キーワード + ベクトル）+ Semantic Ranking のフルスタック構成。
現構成がセマンティック検索のみであれば、ハイブリッド化だけで精度改善が見込める。

### Azure: Azure AI Search

Azure AI Search はセマンティック検索専用ではない。

| 検索タイプ | エンジン | 用途 |
|-----------|---------|------|
| Full-Text / Keyword | BM25（転置インデックス） | 完全一致・部分一致。従来型検索 |
| Vector | HNSW / eKNN | 埋め込みベクトルによる意味的類似検索 |
| Hybrid | BM25 + Vector → RRF 統合 | キーワードとベクトルの併用。精度最良 |
| Semantic Ranking | Microsoft 言語モデル | 上記いずれかの結果に対するリランキング（オプション） |

Semantic Ranking は Azure 独自のマネージド ML リランカー。API パラメータを追加するだけで有効化でき、追加のモデルデプロイが不要。

### AWS: Amazon OpenSearch Service

Amazon OpenSearch Service は Elasticsearch 互換のマネージド検索サービス。OpenSearch 2.x 以降、Neural Search プラグインによるベクトル検索・ハイブリッド検索が強化されている。

| 検索タイプ | エンジン | 用途 |
|-----------|---------|------|
| Full-Text / Keyword | BM25（Lucene） | 完全一致・部分一致。従来型検索 |
| Vector（k-NN） | HNSW / Faiss / Lucene | 埋め込みベクトルによる意味的類似検索 |
| Hybrid | BM25 + k-NN → search pipeline で正規化・統合 | キーワードとベクトルの併用 |
| Reranking | ML Commons プラグイン / Amazon Bedrock Rerank API | 検索結果の再順位付け |

**Azure AI Search との主な違い:**

| 観点 | Azure AI Search | Amazon OpenSearch Service |
|------|-----------------|--------------------------|
| ハイブリッド検索の設定 | API パラメータで指定。設定が簡潔 | search pipeline の事前設定が必要（後述） |
| マネージド ML リランカー | Semantic Ranking（組み込み） | なし。ML Commons または Bedrock Rerank API を利用 |
| サーバーレス版 | なし（SKU でスケール調整） | OpenSearch Serverless（一部プラグイン制限あり） |
| 埋め込み生成 | 統合ベクトル化（インデクサーで自動生成可） | Neural Search プラグイン or アプリ側で生成 |

---

## 4. Pydantic AI + 検索エンジンの接続

### 共通: 接続方式

Pydantic AI はバックエンド非依存の設計。`@agent.tool_plain` でカスタム検索ツールを定義し、ツール内部で検索エンジンの SDK を呼び出す。検索エンジンの差し替えはツール内部の実装を変えるだけで済む。

**公式 RAG サンプル:** Pydantic AI 公式は pgvector + PostgreSQL を使用。Azure AI Search / OpenSearch は差し替え可能。

### Azure: Azure AI Search との接続

```python
from azure.search.documents import SearchClient
from pydantic_ai import Agent

agent = Agent("openai:gpt-4o", system_prompt="...")

@agent.tool_plain
async def search_documents(query: str) -> str:
    """ナレッジベースからドキュメントを検索する"""
    client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(AZURE_SEARCH_KEY),
    )
    results = client.search(
        search_text=query,
        query_type="semantic",          # or "simple" for keyword
        semantic_configuration_name="default",
        vector_queries=[...],           # ハイブリッド検索時
        top=5,
    )
    return "\n---\n".join([r["content"] for r in results])
```

**必要な SDK:** `azure-search-documents`（Azure AI Search の Python SDK）

### AWS: Amazon OpenSearch Service との接続

```python
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
from pydantic_ai import Agent

# AWS 認証（IAM ベース）
session = boto3.Session()
credentials = session.get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    "ap-northeast-1",
    "es",  # OpenSearch Serverless の場合は "aoss"
    session_token=credentials.token,
)

agent = Agent("openai:gpt-4o", system_prompt="...")

@agent.tool_plain
async def search_documents(query: str) -> str:
    """ナレッジベースからドキュメントを検索する"""
    client = OpenSearch(
        hosts=[{"host": OPENSEARCH_ENDPOINT, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        connection_class=RequestsHttpConnection,
    )
    # ハイブリッド検索（BM25 + k-NN）
    body = {
        "query": {
            "hybrid": {
                "queries": [
                    {"match": {"content": query}},
                    {
                        "knn": {
                            "embedding": {
                                "vector": embed(query),
                                "k": 5,
                            }
                        }
                    },
                ]
            }
        }
    }
    results = client.search(
        index=INDEX_NAME,
        body=body,
        params={"search_pipeline": "hybrid-search-pipeline"},
    )
    return "\n---\n".join(
        [hit["_source"]["content"] for hit in results["hits"]["hits"]]
    )
```

**必要な SDK:** `opensearch-py`, `boto3`, `requests-aws4auth`

**事前設定: search pipeline の作成が必要。** Azure AI Search では API パラメータだけでハイブリッド検索を有効化できるが、OpenSearch では検索パイプラインを先に設定する。

```json
PUT /_search/pipeline/hybrid-search-pipeline
{
  "phase_results_processors": [
    {
      "normalization-processor": {
        "normalization": { "technique": "min_max" },
        "combination": {
          "technique": "arithmetic_mean",
          "parameters": { "weights": [0.3, 0.7] }
        }
      }
    }
  ]
}
```

`weights` でキーワード検索とベクトル検索の重み付けを調整できる。上記例ではベクトル検索を 0.7、キーワード検索を 0.3 に設定。

---

## 5. デプロイ先の比較

### Vercel（Python）— 共通

| 項目 | 制約 |
|------|------|
| 実行時間 | Free: 10秒、Pro: 60秒（Fluid Compute で最大800秒） |
| パッケージサイズ | 解凍後 250MB 上限 |
| ファイルシステム | 読み取り専用（`/tmp` のみ書込可） |
| WebSocket | 非対応 |
| バックグラウンド処理 | 不可 |

**判定: LLM エージェントには不向き。** LLM 呼び出しは数秒〜数十秒、エージェントのマルチステップ実行はさらに長くなるため、実行時間制約が厳しい。

FastAPI を Vercel にデプロイすること自体は可能（ゼロコンフィグ対応）だが、RAG エージェントのバックエンドとしては制約が多すぎる。

### AWS Lambda — 不向き

| 項目 | 詳細 |
|------|------|
| 実行時間 | 最大15分 |
| WebSocket | 非対応（API Gateway WebSocket API で疑似対応は可能） |
| レスポンスストリーミング | Lambda Response Streaming で対応可能だが、API Gateway 経由ではバッファリングされる制約あり |
| コールドスタート | あり（数百ms〜数秒） |
| 料金 | リクエスト数 + 実行時間の従量課金。トラフィックが少なければ最安 |

**判定: LLM エージェントには不向き。** 実行時間の15分上限自体は多くのケースで収まるが、本質的な問題は**レスポンスのリアルタイム返却が難しい**点にある。

LLM の回答生成は数秒〜数十秒、エージェンティック RAG の検索→評価→再検索ループでは数十秒〜1分超かかることもある。その間ユーザーにストリーミングで途中経過を返したいが、Lambda ではこれが素直にできない。WebSocket（Chainlit 等のチャット UI が前提とする通信方式）も Lambda 単体では非対応で、API Gateway WebSocket API を組み合わせる必要があり、FastAPI/Chainlit の WebSocket をそのまま動かすのとは設計が大きく変わる。

常駐型のコンテナサービス（Fargate / App Service）であれば、WebSocket もストリーミングもそのまま動作する。

### Railway — 共通

| 項目 | 詳細 |
|------|------|
| 実行時間 | 無制限（常時稼働コンテナ） |
| コールドスタート | なし |
| WebSocket | 完全対応 |
| バックグラウンド処理 | 対応 |
| DB | ワンクリックで Postgres プロビジョニング |
| SSL/LB | 自動設定 |
| デプロイ | GitHub 連携、CLI、Docker |
| 料金 | 分単位の従量課金 |

**判定: Python バックエンド（特に LLM/AI アプリ）に最適。** 実行時間制限なし、WebSocket 対応、DB プロビジョニングが簡単。

### クラウドネイティブなデプロイ先

| | Azure App Service | AWS Fargate（ECS） |
|---|---|---|
| 実行時間 | 無制限 | 無制限 |
| WebSocket | 対応 | 対応（ALB 経由） |
| コンテナ | Docker 対応 | Docker 必須 |
| スケーリング | 自動（プランに応じて） | タスク数ベースの自動スケーリング |
| 料金 | インスタンス課金 | vCPU + メモリの秒単位従量課金 |
| 特徴 | Azure サービスとの統合が容易 | 柔軟な構成、VPC 統合 |

- **Azure 環境 →** Azure App Service
- **AWS 環境 →** Fargate（VPC 統合、柔軟な構成）

### 推奨構成

**Azure 版:**
```
[フロントエンド]          [バックエンド]              [検索]
 Vercel (Next.js)  →  Azure App Service        →  Azure AI Search
                      (FastAPI + Pydantic AI)
```

**AWS 版:**
```
[フロントエンド]          [バックエンド]              [検索]
 Vercel (Next.js)  →  AWS Fargate              →  Amazon OpenSearch
                      (FastAPI + Pydantic AI)      Service
```

いずれも:
- フロントエンド: Vercel（Next.js / React）
- バックエンド: 各クラウドのコンテナサービス（FastAPI + Pydantic AI）
- Observability: クラウド監視サービス + 必要に応じて Langfuse 等の LLM 特化ツール
- 認証: NextAuth.js（フロント主導）or バックエンド側 OAuth2

---

## 6. 認証の選択肢

24,000 名規模の認証が必要。

| 方式 | 概要 | 向いているケース |
|------|------|----------------|
| NextAuth.js | Next.js 組み込み。OAuth / SAML 対応 | フロントエンド主導。SSO 連携 |
| FastAPI + OAuth2 | バックエンド側で認証。JWT トークン | API ファースト。モバイル対応 |
| Auth0 / Clerk | マネージド認証。無料枠あり | 早く立ち上げたい。クラウド非依存 |
| **Azure AD B2C** | Azure ネイティブ。大規模向け | **Azure 基盤との統合** |
| **Amazon Cognito** | AWS ネイティブ。大規模向け | **AWS 基盤との統合** |

### Azure: Azure AD B2C

Azure 基盤なら Azure AD B2C が自然。既存の Azure AD テナントとの統合が容易で、B2C（一般消費者向け）のカスタマイズ可能なサインイン UI を提供する。SAML / OIDC フェデレーション対応。

### AWS: Amazon Cognito

AWS 基盤なら Amazon Cognito が自然。

| 項目 | 詳細 |
|------|------|
| 構成 | ユーザープール（認証）+ ID プール（認可）の二層構成 |
| フェデレーション | SAML 2.0 / OIDC 対応。既存の IdP と連携可能 |
| スケーラビリティ | 数百万ユーザーまでスケール |
| セキュリティ | MFA、パスワードポリシー、アカウントリカバリーが組み込み |
| 料金 | MAU（月間アクティブユーザー）ベースの従量課金。50,000 MAU まで無料枠 |

既存の認証基盤があるなら、それに合わせる。

---

## 7. Chat UI フレームワーク選定

### 結論: デモ用途には Chainlit を採用

| | **Chainlit** | **Gradio** | **Streamlit** |
|---|---|---|---|
| チャット特化度 | ChatGPT風UI。チャット専用設計 | チャット対応だが汎用寄り | ダッシュボード寄り |
| ツールコール可視化 | `@cl.step()` でネスト表示。最強 | `ChatMessage` metadata で表示可能 | `st.status` で手動構築 |
| 最小コード | 約6行 | 約5行 | 約15-20行 |
| 見た目 | 最も洗練（ChatGPT風が標準） | モダンだがデモ感 | 機能的だが地味 |
| 認証 | OAuth（Google, Azure AD, Okta）デコレータ1つ | 弱い | なし |
| Pydantic AI 連携 | 事例多数 | 公式サポート | チュートリアル記事あり |
| リスク | 2025年5月にコアチーム離脱 → コミュニティ運営 | HuggingFace 傘下。安定 | Snowflake 傘下。安定 |

**Chainlit 採用理由:**
- クライアントデモで見栄えがする（ChatGPT風UIが標準装備）
- エージェントのツールコール過程がネスト表示される → エージェンティックRAGの動きを可視化しやすい
- 認証が組み込み（Azure AD 対応）→ 認証デモにも使える
- コアチーム離脱リスクはデモ用途なら問題ない

**デモ用スタック（クラウド非依存）:**
```
Chainlit (Chat UI) + Pydantic AI (Agent) + 検索エンジン (Azure AI Search or OpenSearch)
  ↓
Railway or Docker でデプロイ
```

Pydantic 公式の `ai-chat-ui`（React ベース）も存在するが、Python only の方針に合わない。
本番向けの UI 選定は別途検討する。

---

## 8. エージェントフレームワーク選定の根拠

### AI エージェントの実装アプローチ

3つのアプローチがある。

```
フレームワーク不使用  — LLM API + 自前ループ。完全制御、依存最小
Chain/Graph型        — 自分でフローを組み立てる（LangChain, LangGraph）
Agent Runtime型      — Agent loop が組み込み済み（Pydantic AI, Claude Agent SDK, OpenAI Agents SDK）
```

| アプローチ | 代表 | Agent Loop | 向いているケース |
|-----------|------|-----------|----------------|
| フレームワーク不使用 | LLM API + 自前ループ | 自分で書く（数十行） | 依存を最小にしたい、完全制御が必要 |
| Chain/Graph型 | LangChain, LangGraph | 自分でフロー定義・接続 | 複雑なワークフロー、明示的な制御が必要 |
| Agent Runtime型 | Pydantic AI, Claude Agent SDK, OpenAI Agents SDK | フレームワークに組み込み済み | Single agent、API backend、structured output |

フレームワーク不使用も現実的な選択肢。LLM API 自体がツール呼び出しに対応しており、Agent loop は自作可能。フレームワークのバージョン変更に振り回されない利点がある。

### Pydantic AI（Agent Runtime型）を選ぶ理由

1. **LLM Agnostic**: 20+ プロバイダー対応。Azure OpenAI も公式サポート。Google 等特定ベンダーに縛られない
2. **Agent loop が組み込み済み**: ツール定義だけでエージェントが動く。フローを自分で組み立てる必要がない
3. **型安全**: Pydantic validation + IDE サポート。ツール定義がデコレータ + 型ヒントだけ
4. **LLMOps 対応**: OpenTelemetry ベースで、クラウド監視サービスや Langfuse 等の LLM 特化ツールと統合可能

### LangChain / LangGraph について

LangChain / LangGraph は毀誉褒貶が激しいフレームワークとして知られる。

**主な批判:**
- 抽象化が多すぎて、本来シンプルな LLM アプリを逆に複雑にしている
- バージョン変更が激しく、サンプルやドキュメントがすぐ陳腐化する
- 「Agent framework」というよりは「Workflow 管理」である

**一方で:**
- **v1.0 GA（2025年10月）以降は安定しており、再評価されている**。LangChain v1.2.12 / LangGraph v1.1.0（2026年3月時点）。v0.x 時代の破壊的変更が収まり、実務での信頼性が向上した
- 複雑な分岐・制御フローが必要なケースでは依然として有力な選択肢
- 近藤自身も別案件で LangGraph を活用しており、特に問題は発生していない

**今回 Pydantic AI を選ぶ理由は LangChain の否定ではない。** 用途が Single agent の RAG であり、Agent Runtime型の方がシンプルに実装できるという判断。複雑なワークフロー制御が必要になれば LangGraph も選択肢に入る。

### フレームワーク選定で最も重要なのは LLMOps

フレームワークの機能差は時間とともに収束する。差がつくのは **品質評価（LLMOps）の仕組みが組み込まれているかどうか**。

LLM アプリは従来のソフトウェアと違い、出力の正しさを単体テストで保証できない。本番運用には:
- リクエスト単位のトレース（どのツールが呼ばれ、何が返ったか）
- トークン使用量・コスト・レイテンシの継続的モニタリング
- 検索精度の定量評価（Recall, Precision, MRR 等）
- A/B テストやプロンプト変更の影響測定

が不可欠。Pydantic AI は OpenTelemetry に対応しており、クラウド監視サービス（Application Insights / CloudWatch）や LLM 特化ツール（Langfuse 等）と柔軟に統合できる。特定の Observability ツールに縛られない点が強み。

---

## Sources

### Pydantic AI / LLMOps
- [Pydantic AI 公式ドキュメント](https://ai.pydantic.dev/)
- [Pydantic AI GitHub](https://github.com/pydantic/pydantic-ai)
- [Pydantic AI Changelog](https://ai.pydantic.dev/changelog/)
- [Langfuse](https://langfuse.com/)
- [Pydantic AI RAG Example](https://ai.pydantic.dev/examples/rag/)

### Azure
- [Azure AI Search Overview](https://learn.microsoft.com/en-us/azure/search/search-what-is-azure-search)
- [Azure AI Search Hybrid Search](https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview)
- [Azure AI Search Semantic Ranking](https://learn.microsoft.com/en-us/azure/search/semantic-search-overview)

### AWS
- [Amazon OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/)
- [OpenSearch Hybrid Search](https://opensearch.org/docs/latest/search-plugins/hybrid-search/)
- [OpenSearch k-NN Plugin](https://opensearch.org/docs/latest/search-plugins/knn/index/)
- [Amazon Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/)
- [Amazon Textract](https://docs.aws.amazon.com/textract/latest/dg/)
- [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/)


### デプロイ
- [Vercel Python Runtime](https://vercel.com/docs/functions/runtimes/python)
- [Railway 公式](https://railway.com/)
- [Railway vs Vercel 比較](https://docs.railway.com/platform/compare-to-vercel)
