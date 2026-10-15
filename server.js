const express = require('express');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3000;
const LOG_FILE = path.join(__dirname, 'data', 'logs.jsonl');
const UA =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';

fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });

// ---------- log storage (jsonl) ----------
let logs = [];
let totalBaht = 0;
if (fs.existsSync(LOG_FILE)) {
  for (const line of fs.readFileSync(LOG_FILE, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    try {
      const row = JSON.parse(line);
      logs.push(row);
      totalBaht += Number(row.amount) || 0;
    } catch (_) {}
  }
}

function addLog(row) {
  logs.push(row);
  totalBaht += Number(row.amount) || 0;
  fs.appendFile(LOG_FILE, JSON.stringify(row) + '\n', () => {});
}

// ---------- helpers ----------
function normalizePhone(input) {
  let p = String(input || '').replace(/[^0-9+]/g, '');
  if (p.startsWith('+66')) p = '0' + p.slice(3);
  else if (p.startsWith('66') && p.length === 11) p = '0' + p.slice(2);
  return p;
}

function maskPhone(p) {
  return p.slice(0, 3) + '-xxx-' + p.slice(-4);
}

function extractCode(input) {
  const s = String(input || '').trim();
  const m = s.match(/[?&]v=([0-9A-Za-z]{10,64})/);
  if (m) return m[1];
  if (/^[0-9A-Za-z]{10,64}$/.test(s)) return s;
  return null;
}

const ERR = {
  VOUCHER_NOT_FOUND: 'ไม่พบซองนี้ หรือลิงก์ไม่ถูกต้อง',
  VOUCHER_EXPIRED: 'ซองนี้หมดอายุแล้ว',
  VOUCHER_OUT_OF_STOCK: 'ซองนี้ถูกรับไปหมดแล้ว',
  TARGET_USER_REDEEMED: 'เบอร์นี้เคยรับซองนี้ไปแล้ว',
  CANNOT_GET_OWN_VOUCHER: 'ไม่สามารถรับซองของตัวเองได้',
  TARGET_USER_NOT_FOUND: 'ไม่พบเบอร์นี้ในระบบ TrueMoney',
  INTERNAL_ERROR: 'ระบบ TrueMoney ขัดข้อง ลองใหม่อีกครั้ง',
};

const inFlight = new Set();

async function tmFetch(url, options) {
  const res = await fetch(url, {
    ...options,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'User-Agent': UA,
      ...(options && options.headers),
    },
  });
  let json = null;
  try {
    json = await res.json();
  } catch (_) {}
  return { status: res.status, json };
}

async function redeem(phone, code) {
  // 1) ตรวจซอง + เบอร์ก่อน
  const v = await tmFetch(
    `https://gift.truemoney.com/campaign/vouchers/${code}/verify?mobile=${phone}`,
    { method: 'GET' }
  );
  const vCode = v.json && v.json.status && v.json.status.code;
  if (vCode && vCode !== 'SUCCESS') {
    return { ok: false, code: vCode, message: ERR[vCode] || 'ตรวจสอบซองไม่ผ่าน (' + vCode + ')' };
  }

  // 2) กดรับซอง
  const r = await tmFetch(`https://gift.truemoney.com/campaign/vouchers/${code}/redeem`, {
    method: 'POST',
    body: JSON.stringify({ mobile: phone, voucher_hash: code }),
  });
  const rCode = r.json && r.json.status && r.json.status.code;
  if (rCode !== 'SUCCESS') {
    return {
      ok: false,
      code: rCode || 'UNKNOWN',
      message: ERR[rCode] || 'รับซองไม่สำเร็จ' + (rCode ? ' (' + rCode + ')' : ''),
    };
  }
  const amount = Number(
    (r.json.data && r.json.data.my_ticket && r.json.data.my_ticket.amount_baht) || 0
  );
  const from = (r.json.data && r.json.data.voucher && r.json.data.voucher.owner_full_name) || '-';
  return { ok: true, amount, from };
}

// ---------- app ----------
const app = express();
app.set('trust proxy', true);
app.use(express.json({ limit: '10kb' }));
app.use(express.urlencoded({ extended: false, limit: '10kb' }));

// เปิดสาธารณะ ให้บอท/เว็บอื่นเรียกได้ (CORS)
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

app.use(express.static(path.join(__dirname, 'public')));

app.post('/api/redeem', async (req, res) => {
  const phone = normalizePhone(req.body.phone);
  const code = extractCode(req.body.link || req.body.code);

  if (!/^0[689]\d{8}$/.test(phone)) {
    return res.status(400).json({ ok: false, code: 'BAD_PHONE', message: 'เบอร์โทรไม่ถูกต้อง (ต้องเป็นเบอร์ 10 หลัก เช่น 0812345678)' });
  }
  if (!code) {
    return res.status(400).json({ ok: false, code: 'BAD_LINK', message: 'ลิงก์ซองไม่ถูกต้อง (ต้องเป็นลิงก์ gift.truemoney.com)' });
  }
  if (inFlight.has(code)) {
    return res.status(429).json({ ok: false, code: 'BUSY', message: 'ซองนี้กำลังถูกดำเนินการอยู่' });
  }

  inFlight.add(code);
  try {
    const result = await redeem(phone, code);
    if (!result.ok) return res.status(400).json(result);

    addLog({
      time: new Date().toISOString(),
      phone: maskPhone(phone),
      amount: result.amount,
      from: result.from,
    });
    return res.json({
      ok: true,
      phone,
      amount: result.amount,
      from: result.from,
      message: `รับซองสำเร็จ ${result.amount} บาท เข้าเบอร์ ${phone}`,
    });
  } catch (e) {
    console.error(e);
    return res.status(500).json({ ok: false, code: 'SERVER_ERROR', message: 'เซิร์ฟเวอร์ติดต่อ TrueMoney ไม่ได้ ลองใหม่อีกครั้ง' });
  } finally {
    inFlight.delete(code);
  }
});

app.get('/api/logs', (req, res) => {
  const limit = Math.min(Number(req.query.limit) || 30, 200);
  res.json({
    ok: true,
    total_baht: Math.round(totalBaht * 100) / 100,
    count: logs.length,
    logs: logs.slice(-limit).reverse(),
  });
});

app.listen(PORT, () => console.log('valan.shop running on port ' + PORT));
