/**
 * SendAI Solana Agent Kit — real devnet transactions, bootcamp-safe.
 *
 * What it does (DEVNET ONLY, enforced in code):
 *   1. loads or generates a throwaway keypair (.keypair.json, gitignored)
 *   2. reads network TPS + wallet balance THROUGH the Agent Kit's actions
 *   3. requests faucet funds through the kit's own request_faucet_funds action
 *   4. sends a real (tiny) SOL transfer to itself and prints the signature
 *
 * Guard: refuses to run without DEVNET_LIVE=1, and refuses ANY rpc that is
 * not devnet — the course's no-mainnet-path rule, enforced rather than promised.
 *
 * Run:
 *   pnpm install
 *   DEVNET_LIVE=1 pnpm demo
 */

import { Keypair, LAMPORTS_PER_SOL, PublicKey, Connection } from "@solana/web3.js";
import { KeypairWallet, SolanaAgentKit } from "solana-agent-kit";
import TokenPlugin from "@solana-agent-kit/plugin-token";
import { readFileSync, writeFileSync, existsSync } from "node:fs";

const RPC_URL = "https://api.devnet.solana.com";

function guard(): void {
  if (process.env.DEVNET_LIVE !== "1") {
    console.log("SKIP: set DEVNET_LIVE=1 to run (makes real devnet calls, spends nothing real).");
    process.exit(0);
  }
  if (!RPC_URL.includes("devnet")) {
    throw new Error("refusing to run: RPC is not devnet — this example never touches mainnet");
  }
}

function throwawayKeypair(): Keypair {
  const path = `${__dirname}/.keypair.json`;
  if (existsSync(path)) {
    return Keypair.fromSecretKey(Uint8Array.from(JSON.parse(readFileSync(path, "utf-8"))));
  }
  const kp = Keypair.generate();
  writeFileSync(path, JSON.stringify(Array.from(kp.secretKey)));
  console.log("generated a throwaway devnet keypair (.keypair.json — gitignored, worthless)");
  return kp;
}

async function main() {
  guard();
  const keypair = throwawayKeypair();
  console.log(`buyer (throwaway): ${keypair.publicKey.toBase58()}`);

  const wallet = new KeypairWallet(keypair, RPC_URL);
  const agent = new SolanaAgentKit(wallet, RPC_URL, {}).use(TokenPlugin);
  console.log(`agent kit loaded: ${Object.keys(agent.methods).length} methods from the token plugin`);

  // 1) Reads through the kit's own actions.
  const tps = await agent.methods.getTPS(agent);
  console.log(`devnet TPS via agent kit: ${Math.round(tps)}`);
  let balance = (await agent.methods.get_balance(agent)) ?? 0;
  console.log(`balance via agent kit: ${balance} SOL`);

  // 2) Fund the throwaway through the kit's faucet action (rate-limited; tolerate failure).
  if (balance < 0.05) {
    try {
      console.log("requesting faucet funds via agent kit...");
      await agent.methods.request_faucet_funds(agent);
    } catch (error) {
      console.log(`faucet refused (rate limits are normal): ${String(error).slice(0, 100)}`);
    }
    balance = (await agent.methods.get_balance(agent)) ?? 0;
    console.log(`balance after faucet: ${balance} SOL`);
  }

  if (balance < 0.01) {
    console.log("\nnot enough devnet SOL for a transfer — reads verified, tx skipped honestly.");
    console.log(`fund ${keypair.publicKey.toBase58()} at https://faucet.solana.com and rerun.`);
    return;
  }

  // 3) A REAL transaction: transfer a tiny amount to ourselves.
  //    Small on purpose — the point is the signature and what moved, not the amount.
  const signature = await agent.methods.transfer(
    agent,
    new PublicKey(keypair.publicKey.toBase58()),
    0.001,
  );
  console.log(`\ntransfer sent — signature: ${signature}`);
  console.log(`inspect it: https://explorer.solana.com/tx/${signature}?cluster=devnet`);

  // 4) The bootcamp rule: a signature says it LANDED; the balance delta says
  //    what it DID (Session 13's receipt lesson). Fee paid = the delta.
  const connection = new Connection(RPC_URL, "confirmed");
  const lamports = await connection.getBalance(keypair.publicKey);
  console.log(`post-tx balance: ${lamports / LAMPORTS_PER_SOL} SOL (self-transfer -> only the fee moved)`);

  // 5) SPL leg — devnet USDC, when the wallet holds any: a token transfer is a
  //    DIFFERENT code path (token program, ATAs) and deserves its own receipt.
  const DEVNET_USDC = new PublicKey("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU");
  // Balance read via web3.js: the kit's token-balance helpers assume either
  // Metaplex metadata (absent on devnet USDC) or a token-ACCOUNT address.
  const tokenAccounts = await connection.getParsedTokenAccountsByOwner(keypair.publicKey, {
    mint: DEVNET_USDC,
  });
  const usdcBalance =
    tokenAccounts.value[0]?.account.data.parsed.info.tokenAmount.uiAmount ?? 0;
  if (usdcBalance > 0) {
    console.log(`\ndevnet USDC balance: ${usdcBalance}`);
    const usdcSig = await agent.methods.transfer(
      agent,
      new PublicKey(keypair.publicKey.toBase58()),
      1,
      DEVNET_USDC,
    );
    console.log(`USDC transfer sent — signature: ${usdcSig}`);
    console.log(`inspect it: https://explorer.solana.com/tx/${usdcSig}?cluster=devnet`);
  } else {
    console.log("\nno devnet USDC held — SPL leg skipped (fund via Circle's devnet faucet to try it).");
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
