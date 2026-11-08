// BSC chain scanner (Cloudflare Worker).
// Every 5 min (cron) scan the last ~100 blocks for PairCreated / PoolCreated
// on PancakeSwap V2, PancakeSwap V3 and Biswap.
// Factory addresses verified on-chain 2026-11-09 via eth_getCode / router.factory():
//   Pancake V2 0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73
//   Pancake V3 0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865
//   Biswap     0x858e3312ed3a876947ea49d572a7c42de08af7ee (from router.factory())
// RPC URL must come from env BSC_RPC_URL (Worker Secret, Chainstack).
// Do NOT use public nodes: eth_getLogs on them returns 429/403.
// Do NOT put the RPC URL in this repo.
// topic0 values verified against Bitquery / Dedaub / Uniswap docs (keccak of signature):
//   PairCreated(address,address,address,uint256)
//   PoolCreated(address,address,uint24,int24,address)
export const PAIR_CREATED_TOPIC = "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9";
export const POOL_CREATED_TOPIC = "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118";
export const CHUNK_BLOCKS = 100; // Chainstack eth_getLogs limit

export function parsePairCreatedLog(log, source) {
  // V2/Biswap: topics[1]=token0, topics[2]=token1, data=pair+uint (pair is in data for V2? No:
  // V2 PairCreated(address,address,address,uint256) -> token0,token1 indexed, pair+uint in data)
  if (!log.topics || log.topics.length < 3) return null;
  const token0 = "0x" + log.topics[1].slice(-40);
  const token1 = "0x" + log.topics[2].slice(-40);
  const data = (log.data || "").replace(/^0x/, "");
  const pair = data.length >= 64 ? "0x" + data.slice(24, 64) : null;
  return { source, token0, token1, pair, blockNumber: parseInt(log.blockNumber, 16), txHash: log.transactionHash };
}
export function parsePoolCreatedLog(log, source) {
  // V3 PoolCreated(token0,token1,fee,tickSpacing,pool): token0,token1,fee indexed
  if (!log.topics || log.topics.length < 4) return null;
  const token0 = "0x" + log.topics[1].slice(-40);
  const token1 = "0x" + log.topics[2].slice(-40);
  const fee = parseInt(log.topics[3], 16);
  const data = (log.data || "").replace(/^0x/, "");
  // data word 0 = tickSpacing, word 1 = pool address
  const pool = data.length >= 128 ? "0x" + data.slice(64 + 24, 64 + 64) : null;
  return { source, token0, token1, fee, pair: pool, blockNumber: parseInt(log.blockNumber, 16), txHash: log.transactionHash };
}

async function rpc(env, method, params) {
  const res = await fetch(env.BSC_RPC_URL, { method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", method, params, id: 1 }) });
  const j = await res.json();
  if (j.error) throw new Error(`RPC ${method}: ${JSON.stringify(j.error)}`);
  return j.result;
}

export async function scan(env) {
  if (!env.BSC_RPC_URL) return { ok: false, error: "BSC_RPC_URL secret not set (Chainstack)" };
  const latest = parseInt(await rpc(env, "eth_blockNumber", []), 16);
  const from = latest - CHUNK_BLOCKS;
  const factories = [
    { name: "pancakeswap-v2", address: "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73", topic: PAIR_CREATED_TOPIC, parse: parsePairCreatedLog },
    { name: "biswap", address: "0x858e3312ed3a876947ea49d572a7c42de08af7ee", topic: PAIR_CREATED_TOPIC, parse: parsePairCreatedLog },
    { name: "pancakeswap-v3", address: "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865", topic: POOL_CREATED_TOPIC, parse: parsePoolCreatedLog },
  ];
  const leads = [];
  for (const f of factories) {
    const logs = await rpc(env, "eth_getLogs", [{ fromBlock: "0x" + from.toString(16), toBlock: "0x" + latest.toString(16), address: f.address, topics: [f.topic] }]);
    for (const log of logs || []) {
      const p = f.parse(log, f.name);
      if (p) leads.push({ ...p, token_status: "has_token", chain: 56, verified: false, verification: "未核验", first_seen: new Date().toISOString().slice(0, 10) });
    }
  }
  // Persist cursor + leads in D1 if bound, otherwise just return them.
  if (env.DB) {
    await env.DB.prepare("INSERT OR REPLACE INTO scans (id, from_block, to_block, pairs_seen, candidates, scanned_at) VALUES (1, ?, ?, ?, ?, ?)").bind(from, latest, leads.length, leads.length, new Date().toISOString()).run();
    for (const l of leads) {
      await env.DB.prepare("INSERT OR IGNORE INTO chain_leads (pair, token0, token1, source, block_number, tx_hash, first_seen) VALUES (?, ?, ?, ?, ?, ?, ?)").bind(l.pair, l.token0, l.token1, l.source, l.blockNumber, l.txHash, l.first_seen).run();
    }
  }
  return { ok: true, from_block: from, to_block: latest, pairs_seen: leads.length, candidates: leads.length, leads };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/chain-leads") {
      if (!env.DB) return Response.json({ ok: true, configured: false, leads: [], note: "D1 not bound yet" });
      const rows = await env.DB.prepare("SELECT * FROM chain_leads ORDER BY block_number DESC LIMIT 50").all();
      return Response.json({ ok: true, configured: true, leads: rows.results || [] });
    }
    if (url.pathname === "/api/chain-leads/health") return Response.json({ ok: true, configured: !!env.BSC_RPC_URL, d1: !!env.DB });
    return Response.json({ ok: true, service: "bsc-agent-radar chain scanner", endpoints: ["/api/chain-leads", "/api/chain-leads/health"] });
  },
  async scheduled(_event, env, ctx) { ctx.waitUntil(scan(env).catch(e => console.error(e))); },
};
