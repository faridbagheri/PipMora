/* PipMora indicative FX ticker.
 * biquote.io supplies MT5 quotes and open daily candles. Never infer a 5-decimal
 * price change from a 2-decimal percentage, or present stale quotes as live.
 * Display only; never use these prices for paper-trading execution.
 */
(function () {
  "use strict";
  const PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "EURGBP"];
  const API = "https://biquote.io/api";
  const track = document.querySelector("#preciseTicker .precise-ticker-track");
  const status = document.getElementById("preciseTickerStatus");
  if (!track || !status) return;

  const opens = new Map();
  const quotes = new Map();
  let quoteRunning = false;
  let openRunning = false;
  let pausedUntil = 0;
  const displayPair = code => code.slice(0, 3) + "/" + code.slice(3);
  const fmt = n => Number(n).toFixed(5);
  const valid = n => typeof n === "number" && Number.isFinite(n) && n > 0;
  function setMessage(message) { status.textContent = message; }
  async function getJSON(url) {
    const abort = new AbortController();
    const timeout = setTimeout(() => abort.abort(), 9000);
    try {
      const res = await fetch(url, {cache:"no-store", signal:abort.signal});
      if (res.status === 429) { pausedUntil = Date.now() + 60000; throw Error("Rate limit reached"); }
      if (!res.ok) throw Error("HTTP " + res.status);
      return await res.json();
    } finally { clearTimeout(timeout); }
  }
  function update() {
    for (const code of PAIRS) {
      const item = track.querySelector('[data-symbol="' + code + '"]');
      if (!item) continue;
      const value = item.querySelector(".precise-rate");
      const delta = item.querySelector(".precise-change");
      const tag = item.querySelector(".precise-market-state");
      const tick = quotes.get(code);
      const open = opens.get(code);
      value.textContent = tick && valid(tick.mid) ? fmt(tick.mid) : "—";
      delta.classList.remove("up", "down");
      item.classList.remove("is-live", "is-closed");
      if (!tick) {
        delta.textContent = "—";
        tag.textContent = "Unavailable";
        continue;
      }
      const age = Date.parse(tick.timestamp || "");
      const fresh = tick.marketState === "open" && tick.stale === false &&
        Number.isFinite(age) && Date.now() - age < 300000 && Date.now() - age > -90000;
      item.classList.add(fresh ? "is-live" : "is-closed");
      tag.textContent = fresh ? "LIVE · indicative" : (tick.marketState === "closed" ? "Market closed" : "Stale quote");
      item.title = "Source: " + (tick.source || "biquote.io MT5") + ". Last quote: " + (tick.timestamp || "unknown");
      if (fresh && valid(open)) {
        const diff = tick.mid - open;
        delta.textContent = (diff >= 0 ? "+" : "−") + fmt(Math.abs(diff));
        delta.classList.add(diff >= 0 ? "up" : "down");
        delta.title = "Quote mid-price minus the source's daily opening price";
      } else {
        delta.textContent = "—";
        delta.title = "Session change unavailable or market closed";
      }
    }
  }
  async function refreshDailyOpens() {
    if (openRunning || Date.now() < pausedUntil) return;
    openRunning = true;
    try {
      await Promise.all(PAIRS.map(async code => {
        try {
          const data = await getJSON(API + "/" + code + "/ohlc?interval=1d&limit=2");
          if (!Array.isArray(data.bars)) return;
          const latest = data.bars.find(b => b.isOpen === true) || data.bars[0];
          if (latest && valid(Number(latest.open))) opens.set(code, Number(latest.open));
        } catch (_) {
          // No invented opening price. Show "—" until an open can be fetched.
        }
      }));
    } finally { openRunning = false; update(); }
  }
  async function refreshQuotes() {
    if (quoteRunning || document.hidden || Date.now() < pausedUntil) return;
    quoteRunning = true;
    try {
      const qs = PAIRS.map(s => "symbols=" + encodeURIComponent(s)).join("&");
      const data = await getJSON(API + "/latest?" + qs);
      // Documented batch shape: {EURUSD: {mid, timestamp, ...}, ...}
      const mapped = Array.isArray(data) ? Object.fromEntries(data.map(t => [t.symbol, t])) :
        (data && typeof data === "object" ? data : {});
      let count = 0;
      for (const code of PAIRS) {
        const tick = mapped[code];
        if (tick && valid(Number(tick.mid))) {
          quotes.set(code, {...tick, mid:Number(tick.mid)});
          count++;
        }
      }
      setMessage(count ? "MT5 indicative FX quotes · updates every 15s" : "Quote feed unavailable");
    } catch (_) {
      setMessage("Quote feed unavailable · retrying");
      // Explicitly mark previous data stale rather than leaving a green 'live' badge.
      for (const [key, tick] of quotes) quotes.set(key, {...tick, stale:true});
    } finally { quoteRunning = false; update(); }
  }
  track.addEventListener("click", event => {
    const button = event.target.closest("button[data-symbol]");
    if (!button || !track.contains(button)) return;
    const code = button.dataset.symbol;
    if (!PAIRS.includes(code)) return;
    const selector = document.getElementById("heroPairSelect");
    if (selector) {
      selector.value = code;
      selector.dispatchEvent(new Event("change", {bubbles:true}));
    }
  });
  refreshDailyOpens().then(refreshQuotes);
  const quoteInterval = setInterval(refreshQuotes, 15000);
  const openInterval = setInterval(refreshDailyOpens, 20 * 60 * 1000);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) { refreshQuotes(); refreshDailyOpens(); }
  });
  window.addEventListener("pagehide", () => {
    clearInterval(quoteInterval);
    clearInterval(openInterval);
  }, {once:true});
})();
