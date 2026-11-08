# BSC Agent Radar

只做 **BNB Smart Chain（Chain ID 56）** 的 Agent 项目早期发现聚合站。

- 只要是关于 Agent 的项目都收，不管是否发币
- 目录分三类：**有币 / 无币 / 未知**，无币项目不会因为没合约、没 Mint 就被过滤
- 不连钱包、不交易、不做安全审计背书，所有条目默认 **未核验**

## 来源

| 来源 | 频率 | 说明 |
| --- | --- | --- |
| GitHub API | 每小时 | 搜 BSC + Agent 相关新仓库/更新，不要求含合约地址 |
| X API v2 | 每天多次 | Agent ID、Agentic Wallet、中文智能体，不要求同时命中 launch/mint |
| BNB 官方 / Binance Skills Hub | 每小时 | 官方生态、Skills 清单（GitHub 仓库） |
| 链上扫描（Cloudflare Worker） | 每 5 分钟 | PancakeSwap V2/V3 + Biswap `PairCreated`，只看币 |
| Binance meme-rush（Four.meme） | 补充 | 只看币，不做主发现源 |

## 数据

- `data/catalog.json` — 可见目录：有官网或 GitHub 描述的项目
- `data/review_queue.json` — 待复核线索：新发现先放这里，不直接进目录
- `data/chain_leads.json` — 链上新对候选（Worker 写 D1，同步后也落这里）

## 本地运行

```bash
python3 scripts/test_discover.py          # 离线测试，不联网
python3 scripts/run_discovery.py --help   # 真实发现（需要网络；X 需要 X_BEARER_TOKEN）
node --test worker/test/worker.test.mjs    # Worker 离线测试
```

## 部署

- 前端：GitHub Pages（`.github/workflows/deploy-pages.yml`）
- 发现：GitHub Actions 每小时（`.github/workflows/discover.yml`）
- 链上：Cloudflare Worker，见 `worker/README.md`。部署需要 `CLOUDFLARE_API_TOKEN`、`BSC_RPC_URL`（Chainstack，见 Worker Secret），缺了就停下，不要猜。

## 成本

GitHub Pages + Actions + Cloudflare Workers/D1 免费档，零现金成本。不买服务器，不用付费 API。
