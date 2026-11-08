import test from "node:test";
import assert from "node:assert/strict";
import { parsePairCreatedLog, parsePoolCreatedLog, PAIR_CREATED_TOPIC, POOL_CREATED_TOPIC, CHUNK_BLOCKS } from "../src/index.js";

test("topics are 32-byte hashes", () => {
  assert.equal(PAIR_CREATED_TOPIC.length, 66);
  assert.equal(POOL_CREATED_TOPIC.length, 66);
  assert.equal(PAIR_CREATED_TOPIC, "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9");
  assert.equal(POOL_CREATED_TOPIC, "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118");
  assert.equal(CHUNK_BLOCKS, 100);
});

test("parse V2 PairCreated log", () => {
  const token0 = "0x" + "aa".repeat(20), token1 = "0x" + "bb".repeat(20), pair = "0x" + "cc".repeat(20);
  const log = { topics: [PAIR_CREATED_TOPIC, "0x000000000000000000000000" + token0.slice(2), "0x000000000000000000000000" + token1.slice(2)],
    data: "0x000000000000000000000000" + pair.slice(2) + "0000000000000000000000000000000000000000000000000000000000000001",
    blockNumber: "0x10", transactionHash: "0x" + "dd".repeat(32) };
  const p = parsePairCreatedLog(log, "pancakeswap-v2");
  assert.equal(p.token0.toLowerCase(), token0);
  assert.equal(p.token1.toLowerCase(), token1);
  assert.equal(p.pair.toLowerCase(), pair);
  assert.equal(p.blockNumber, 16);
});

test("parse V3 PoolCreated log (pool is data word 1)", () => {
  const token0 = "0x" + "aa".repeat(20), token1 = "0x" + "bb".repeat(20), pool = "0x" + "cc".repeat(20);
  const log = { topics: [POOL_CREATED_TOPIC, "0x000000000000000000000000" + token0.slice(2), "0x000000000000000000000000" + token1.slice(2), "0x00000000000000000000000000000000000000000000000000000000000001f4"],
    data: "0x" + "00".repeat(31) + "3c" + "000000000000000000000000" + pool.slice(2),
    blockNumber: "0x20", transactionHash: "0x" + "ee".repeat(32) };
  const p = parsePoolCreatedLog(log, "pancakeswap-v3");
  assert.equal(p.fee, 500);
  assert.equal(p.pair.toLowerCase(), pool);
});

test("parse returns null on short topics", () => {
  assert.equal(parsePairCreatedLog({ topics: [] }, "x"), null);
  assert.equal(parsePoolCreatedLog({ topics: [POOL_CREATED_TOPIC] }, "x"), null);
});
