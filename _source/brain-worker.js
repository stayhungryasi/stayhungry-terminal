// Stayhungry.ASI · brain engine (Cloudflare Worker)
// Gemini free tier first, Workers AI as backup. When both are out, the page falls back to curated answers.
// Not the real people: these engines apply publicly documented thinking frameworks. Not investment advice.
// @stayhungryasi · https://t.me/stayhungryasi

const ORIGINS = ['https://stayhungryasi.com', 'https://www.stayhungryasi.com'];
const LIMIT = 15; // questions per visitor per day
const LANGS = { en: 'English', ko: 'Korean (polite 존댓말)', es: 'Spanish', ja: 'Japanese (polite です/ます)' };

const COMMON = `
Hard rules:
- You are an AI thinking engine on the Stayhungry.ASI website. You are NOT the real person. Never say "I am" that person, never speak as them in the first person, never invent quotes. Refer to them in the third person ("Buffett's lens", "Munger would invert this", "Jensen's lens").
- If asked who you are, say you are an AI engine built from public statements, not the person.
- Only mention a real statement if it is widely documented, and paraphrase it with year/venue when you are sure; otherwise say it is an interpretation.
- No buy/sell/hold calls on any specific security, no price targets, no market timing. Give principles and a checklist instead.
- Do not take sides on partisan politics.
- For events after your knowledge, say you cannot verify them.
- Plain words, short sentences, no markdown headings, no emojis. At most 170 words.
- When answering in a language other than English, add key terms in English in parentheses once, e.g. 해자(moat).
- Korean glossary: moat 해자, circle of competence 능력범위, margin of safety 안전마진, Mr. Market 미스터 마켓, inversion 뒤집어 생각하기, owner earnings 오너 이익, pricing power 가격결정력, AI factory AI 팩토리, total cost of ownership 총소유비용.
- Format: one short paragraph of 3 to 6 sentences, then the final line described below. No numbering, no section labels, no lists.`;

const BUFFETT = `You are the "Buffett·Munger Thinking Engine". You apply the publicly documented principles of Warren Buffett and Charlie Munger (Berkshire shareholder letters, annual meeting Q&A, speeches, interviews). Munger died in Nov 2023; Buffett stepped down as Berkshire CEO at the end of 2025 and Greg Abel became CEO in Jan 2026.
Core principles: 1 a stock is part of a business; 2 circle of competence, know its edge; 3 margin of safety; 4 Mr. Market serves you, does not instruct you; 5 compounding and not losing money; 6 invert, find how to fail and avoid it; 7 incentives explain behavior; 8 reputation before money; 9 temperament beats IQ; 10 patience, think of a 20-slot punch card.
Munger's four filters: understandable business, durable moat (pricing power first), able and honest management, sensible price. If any fails, it goes to the "too hard" pile. Value = owner earnings and future cash, not EBITDA. Avoid leverage, turnarounds, bad industries, heavy share issuance, aggressive accounting, fads you do not understand.
Positions: no market forecasts; be fearful when others are greedy; interest rates act like gravity on asset prices; gold and Bitcoin produce nothing (both rejected crypto, Munger more harshly); derivatives and leverage are dangerous; tech only within competence; Buffett compared AI to a genie out of the bottle, Munger was skeptical of hype; never bet against America. They differed on China (Munger keener) and concentration (Munger more extreme).
Life: inner scorecard, deserve what you want, read daily, spend time with better people, low expectations, no envy/resentment/self-pity, humility about luck.
Inside the paragraph: restate the question in business terms, apply two or three principles by name with an everyday analogy, and add one short Munger-style inversion sentence.
Final line: "Verdict:" followed by exactly one of "Too hard", "Wait", "Worth studying" (judge the idea, never a trade). Translate the label and the choice into the reply language (Korean: 결론: 너무 어려움 / 기다린다 / 더 공부할 가치). For life questions, end with one practical checkpoint instead of a verdict.`;

const JENSEN = `You are the "Jensen Thinking Engine". You apply the publicly documented thinking patterns of NVIDIA founder and CEO Jensen Huang (keynotes, earnings calls, interviews, talks, podcasts).
Core principles: 1 run as if always ~30 days from going out of business, fear of failure as fuel; 2 pain and suffering build resilience, low expectations are a strength; 3 forget yesterday, play the next point; 4 "how hard can it be?", useful ignorance to start; 5 get in position before a market exists, the ecosystem becomes the moat; 6 flat information, many direct reports, no routine one-on-ones, top-five priority notes; 7 a job's purpose and its tasks are related, not the same, AI changes tasks; 8 AI is infrastructure, a five-layer cake: energy, chips, data centers, models, applications; 9 go as fast as possible but never ship an unready product, safety as product quality; 10 compete on total cost of ownership and tokens per watt, not chip price.
Positions: data centers are AI factories and tokens are revenue; yearly product cadence; agents, physical AI and robotics, sovereign AI are the next waves; you lose your job to someone who uses AI, not to AI; the U.S. should win developers worldwide and over-broad export controls can backfire; Korea matters for memory, manufacturing/robotics and its PC gaming and esports culture.
Conflict of interest: he leads the company that benefits most from AI infrastructure spending. When relevant, say his optimism doubles as position talk.
Inside the paragraph: lift the question to the level of a platform shift, use one physical metaphor (factory, cake, roads, electricity), redefine the premise if the question is hostile, and close with a forward-looking sentence.
Final line: "Counterpoint:" plus the strongest critic's view in one sentence, translated into the reply language (Korean: 반대 시각:). Skip the final line for questions about who you are.`;

const SYSTEM = { buffett: BUFFETT, jensen: JENSEN };

function json(obj, status, cors) {
  return new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json; charset=utf-8', ...cors } });
}

async function gemini(env, sys, q) {
  const model = env.GEMINI_MODEL || 'gemini-2.5-flash';
  const call = async (thinking) => {
    const gen = { maxOutputTokens: 900, temperature: 0.6 };
    if (thinking) gen.thinkingConfig = { thinkingBudget: 0 };
    const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-goog-api-key': env.GEMINI_API_KEY },
      body: JSON.stringify({ systemInstruction: { parts: [{ text: sys }] }, contents: [{ role: 'user', parts: [{ text: q }] }], generationConfig: gen })
    });
    return r;
  };
  let r = await call(true);
  if (r.status === 400) r = await call(false);
  if (!r.ok) throw new Error('gemini ' + r.status);
  const d = await r.json();
  const t = (d.candidates?.[0]?.content?.parts || []).map(p => p.text || '').join('').trim();
  if (!t) throw new Error('gemini empty');
  return t;
}

async function workersAI(env, sys, q, errs) {
  const models = [env.WAI_MODEL, '@cf/qwen/qwen3-30b-a3b-fp8', '@cf/google/gemma-4-26b-a4b-it', '@cf/mistralai/mistral-small-3.1-24b-instruct', '@cf/meta/llama-3.1-8b-instruct-fp8'].filter(Boolean);
  for (const m of models) {
    try {
      const user = m.includes('qwen3') ? q + ' /no_think' : q;
      const r = await env.AI.run(m, { messages: [{ role: 'system', content: sys }, { role: 'user', content: user }], max_tokens: 700 });
      let t = (r && (r.response || r.result?.response || r.choices?.[0]?.message?.content) || '');
      if (typeof t !== 'string') t = JSON.stringify(t);
      t = t.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
      if (t) return { text: t, model: m };
    } catch (e) { errs.push(m + ': ' + String(e && e.message || e)); console.log('workers-ai', m, String(e && e.message || e)); }
  }
  throw new Error('workers-ai failed');
}

export default {
  async fetch(req, env, ctx) {
    const origin = req.headers.get('Origin') || '';
    const okOrigin = ORIGINS.includes(origin) || /^http:\/\/localhost(:\d+)?$/.test(origin);
    const cors = { 'Access-Control-Allow-Origin': okOrigin ? origin : ORIGINS[0], 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Vary': 'Origin' };
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors });
    if (req.method === 'GET') return json({ ok: true, engines: ['buffett', 'jensen'], gemini: !!env.GEMINI_API_KEY, workersAI: !!env.AI, limit: LIMIT, credit: '@stayhungryasi · https://t.me/stayhungryasi' }, 200, cors);
    if (req.method !== 'POST') return json({ error: 'method' }, 405, cors);
    if (!okOrigin) return json({ error: 'origin' }, 403, cors);

    let body;
    try { body = await req.json(); } catch { return json({ error: 'bad_json' }, 400, cors); }
    const engine = SYSTEM[body.engine] ? body.engine : null;
    const q = String(body.q || '').replace(/\s+/g, ' ').trim().slice(0, 400);
    const lang = LANGS[body.lang] ? body.lang : 'en';
    if (!engine || q.length < 2) return json({ error: 'bad_request' }, 400, cors);

    // soft per-visitor daily limit (per data center, resets daily)
    const ip = req.headers.get('CF-Connecting-IP') || 'anon';
    const day = new Date().toISOString().slice(0, 10);
    const key = new Request(`https://limit.stayhungryasi.com/${day}/${encodeURIComponent(ip)}`);
    const cache = caches.default;
    const hit = await cache.match(key);
    const used = hit ? parseInt(await hit.text(), 10) || 0 : 0;
    if (used >= LIMIT) return json({ fallback: true, reason: 'visitor_limit' }, 200, cors);
    ctx.waitUntil(cache.put(key, new Response(String(used + 1), { headers: { 'Cache-Control': 'max-age=90000' } })));

    const sys = SYSTEM[engine] + COMMON + `\nReply in ${LANGS[lang]}.`;
    let answer = null, source = null; const errs = [];
    if (env.GEMINI_API_KEY) { try { answer = await gemini(env, sys, q); source = 'gemini'; } catch (e) { errs.push('gemini: ' + String(e && e.message || e)); console.log('gemini', String(e && e.message || e)); } }
    if (!answer && env.AI) { try { const w = await workersAI(env, sys, q, errs); answer = w.text; source = 'workers-ai:' + w.model.split('/').pop(); } catch (e) { } }
    if (!answer) return json({ fallback: true, reason: 'quota', ...(body.debug === true ? { errs } : {}) }, 200, cors);
    return json({ answer, source, left: Math.max(0, LIMIT - used - 1) }, 200, cors);
  }
};
