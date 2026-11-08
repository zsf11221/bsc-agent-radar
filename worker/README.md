# Chain Worker

每 5 分钟扫 PancakeSwap V2 / V3 + Biswap 的新对（`PairCreated` / `PoolCreated`）。

## 部署（需要用户在自己浏览器里做，我方不替用户建 Token）

缺以下任一就停下，不要硬推：

1. Cloudflare API Token（Workers Scripts Edit + D1 Edit 权限）
2. D1 数据库 `bsc-agent-radar-chain`，把 `database_id` 填进 `worker/wrangler.toml`
3. Chainstack BSC RPC：`wrangler secret put BSC_RPC_URL`，不要写进仓库、不要用公开节点（公开节点 `eth_getLogs` 返回 -32005 / 429 / 403，已实测）

```sql
-- D1 迁移（建库后执行）
CREATE TABLE IF NOT EXISTS scans (id INTEGER PRIMARY KEY, from_block INTEGER, to_block INTEGER, pairs_seen INTEGER, candidates INTEGER, scanned_at TEXT);
CREATE TABLE IF NOT EXISTS chain_leads (pair TEXT PRIMARY KEY, token0 TEXT, token1 TEXT, source TEXT, block_number INTEGER, tx_hash TEXT, first_seen TEXT);
```

```bash
cd worker
npx wrangler deploy
curl https://<worker域名>/api/chain-leads/health
```

## 离线测试

```bash
node --test worker/test/worker.test.mjs
```
