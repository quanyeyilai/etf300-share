/**
 * 把明文数据加密打包成 docs/data/bundle.js
 *
 * 原理
 * ----
 * 1. 随机生成主密钥 MK（AES-256）
 * 2. 用 MK 加密全部数据（data / macro / sector），密文公开放在页面里
 * 3. 每个账号用「密码 + 随机 salt」经 PBKDF2(SHA-256, 20 万次) 派生 KEK，
 *    再用 KEK 加密 MK，得到该账号专属的一份 wrapped key
 * 4. 登录时：密码 → KEK → 解开 MK → 解开数据
 *
 * 结果：不知道密码的人，即使下载了整个 HTML / 直接看源码，也拿不到任何数据。
 *
 * 用法：node protect.js
 * 账号在 data/users.txt（每行：账号 密码，该文件不入库）
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { subtle } = crypto.webcrypto;

const BASE = __dirname;
const DATA_DIR = path.join(BASE, 'docs', 'data');
const USERS = path.join(BASE, 'data', 'users.txt');
const OUT = path.join(DATA_DIR, 'bundle.js');
const ITER = 200000;

const b64 = (buf) => Buffer.from(buf).toString('base64');

function parseJs(pathStr) {
  const t = fs.readFileSync(pathStr, 'utf-8');
  return JSON.parse(t.slice(t.indexOf('=') + 1).trim().replace(/;+$/, ''));
}

async function kekFrom(pw, salt) {
  const base = await subtle.importKey('raw', Buffer.from(pw, 'utf-8'), 'PBKDF2', false, ['deriveKey']);
  return subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: ITER, hash: 'SHA-256' },
    base, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']
  );
}

async function main() {
  const bundle = {};
  for (const [key, file] of [['data', 'data.js'], ['macro', 'macro.js'], ['sector', 'sector.js']]) {
    const p = path.join(DATA_DIR, file);
    bundle[key] = fs.existsSync(p) ? parseJs(p) : null;
  }

  const raw = Buffer.from(JSON.stringify(bundle), 'utf-8');
  const mk = crypto.randomBytes(32);
  const key = await subtle.importKey('raw', mk, { name: 'AES-GCM' }, false, ['encrypt']);
  const nonce = crypto.randomBytes(12);
  const ct = new Uint8Array(await subtle.encrypt({ name: 'AES-GCM', iv: nonce }, key, raw));

  // 账号列表：优先本地文件；云端（GitHub Actions）由 Secret ETF_USERS 提供
  if (!fs.existsSync(USERS)) {
    const env = (process.env.ETF_USERS || '').trim();
    if (env) {
      fs.mkdirSync(path.dirname(USERS), { recursive: true });
      fs.writeFileSync(USERS, env + '\n', 'utf-8');
      console.log('已从环境变量 ETF_USERS 读取账号');
    } else {
      console.error('缺少账号配置。');
      console.error('  本地：python set_user.py 账号 密码');
      console.error('  云端：在仓库 Secrets 里添加 ETF_USERS（内容：账号 密码，可多行）');
      process.exit(1);
    }
  }
  const accounts = [];
  for (const line of fs.readFileSync(USERS, 'utf-8').split(/\r?\n/)) {
    const s = line.trim();
    if (!s || s.startsWith('#')) continue;
    const parts = s.split(/\s+/);
    if (parts.length < 2) continue;
    const user = parts[0];
    const pw = parts.slice(1).join(' ');
    const salt = crypto.randomBytes(16);
    const kek = await kekFrom(pw, salt);
    const wn = crypto.randomBytes(12);
    const wrapped = new Uint8Array(await subtle.encrypt({ name: 'AES-GCM', iv: wn }, kek, mk));
    accounts.push({ u: user, s: b64(salt), n: b64(wn), k: b64(wrapped) });
  }
  if (!accounts.length) {
    console.error('data/users.txt 里没有有效账号');
    process.exit(1);
  }

  const payload = {
    v: 1, iter: ITER, nonce: b64(nonce), ct: b64(ct),
    accounts, updatedAt: new Date().toISOString()
  };
  fs.writeFileSync(OUT, 'window.ETF_BUNDLE = ' + JSON.stringify(payload) + ';\n', 'utf-8');
  console.log('已加密打包：' + OUT + '（'
    + (fs.statSync(OUT).size / 1024).toFixed(0) + ' KB，'
    + accounts.length + ' 个账号：' + accounts.map(a => a.u).join('、') + '）');
}

main().catch(e => { console.error(e); process.exit(1); });
