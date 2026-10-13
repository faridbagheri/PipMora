/* PipMora forex ticker: a continuously scrolling quote tape.
   biquote.io streams real ticks over SignalR. If WebSockets are unavailable,
   request one batch of six symbols every second (respecting rate limits).
   Only provider prices are displayed; we never interpolate imaginary ticks.
*/
(function () {
  "use strict";
  const PAIRS = ["EURUSD","GBPUSD","USDJPY","USDCHF","AUDUSD","EURGBP"];
  const API = "https://biquote.io/api";
  const track = document.querySelector("#preciseTicker .precise-ticker-track");
  const status = document.getElementById("preciseTickerStatus");
  if (!track || !status) return;

  // The duplicate sequence makes the CSS animation loop without a visible jump.
  // Duplicate buttons are mouse-clickable, but hidden from keyboard and screen readers.
  for (const original of Array.from(track.querySelectorAll("button[data-symbol]"))) {
    const duplicate = original.cloneNode(true);
    const code = duplicate.dataset.symbol;
    delete duplicate.dataset.symbol;
    duplicate.dataset.cloneSymbol = code;
    duplicate.setAttribute("aria-hidden","true");
    duplicate.tabIndex = -1;
    track.appendChild(duplicate);
  }
  const opens = new Map(), quotes = new Map();
  const fmt = value => Number(value).toFixed(5);
  const valid = value => Number.isFinite(value) && value > 0;
  let fetching = false, fetchingOpens = false, suspendedUntil = 0;
  let streaming = false, connection = null, disposed = false;
  const setMessage = value => { status.textContent = value; };

  async function fetchJSON(url) {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(),8000);
    try {
      const response = await fetch(url,{cache:"no-store",signal:ac.signal});
      if (response.status === 429) {
        const retry = Number(response.headers.get("Retry-After"));
        suspendedUntil = Date.now() + (valid(retry) ? retry : 60) * 1000;
        throw Error("Rate limit");
      }
      if (!response.ok) throw Error("HTTP " + response.status);
      return await response.json();
    } finally { clearTimeout(timer); }
  }

  function render() {
    for (const code of PAIRS) {
      const tick = quotes.get(code), open = opens.get(code);
      const time = tick ? Date.parse(tick.timestamp || "") : NaN;
      const fresh = !!tick && tick.marketState === "open" && tick.stale === false &&
        Number.isFinite(time) && Date.now() - time < 300000 && Date.now() - time > -90000;
      const change = fresh && valid(open) ? tick.mid - open : null;
      for (const item of track.querySelectorAll('button[data-symbol="'+code+'"],button[data-clone-symbol="'+code+'"]')) {
        item.querySelector(".precise-rate").textContent = tick && valid(tick.mid) ? fmt(tick.mid) : "—";
        const diff = item.querySelector(".precise-change");
        const percent = item.querySelector(".precise-percent");
        diff.classList.remove("up","down");
        diff.textContent = change === null ? "—" : (change >= 0 ? "+" : "−") + fmt(Math.abs(change));
        if (change !== null) diff.classList.add(change >= 0 ? "up" : "down");
        if (percent) {
          percent.classList.remove("up","down");
          percent.textContent = change === null ? "—" : "(" + (change >= 0 ? "+" : "−") + (Math.abs(change / open) * 100).toFixed(2) + "%)";
          if (change !== null) percent.classList.add(change >= 0 ? "up" : "down");
        }
        const tag = item.querySelector(".precise-market-state");
        if (tag) tag.textContent = ""; // No visible LIVE / indicative badges.
        const state = tick ? (tick.marketState === "closed" ? "Market closed" :
          fresh ? "Current quote" : "Last known quote") : "Price unavailable";
        item.title = code.slice(0,3)+"/"+code.slice(3)+": "+state+
          (tick && tick.timestamp ? " · "+tick.timestamp : "");
      }
    }
  }

  function accept(tick) {
    if (disposed) return;
    const candidate = Array.isArray(tick) ? tick[0] : tick;
    if (!candidate || !PAIRS.includes(candidate.symbol)) return;
    const price = Number(candidate.mid);
    if (!valid(price)) return;
    quotes.set(candidate.symbol,{...candidate,mid:price});
    render();
  }

  async function daily() {
    if (fetchingOpens || Date.now() < suspendedUntil) return;
    fetchingOpens = true;
    try {
      await Promise.all(PAIRS.map(async code => {
        try {
          const data = await fetchJSON(API+"/"+code+"/ohlc?interval=1d&limit=2");
          if (!Array.isArray(data.bars)) return;
          const bar = data.bars.find(b => b.isOpen === true) || data.bars[0];
          if (bar && valid(Number(bar.open))) opens.set(code,Number(bar.open));
        } catch (_) { /* Unknown daily open stays unknown. */ }
      }));
    } finally { fetchingOpens = false; render(); }
  }

  async function poll() {
    if (disposed || document.hidden || streaming || fetching || Date.now() < suspendedUntil) return;
    fetching = true;
    try {
      const query = PAIRS.map(s => "symbols="+encodeURIComponent(s)).join("&");
      const data = await fetchJSON(API+"/latest?"+query);
      const batch = Array.isArray(data) ? Object.fromEntries(data.map(t => [t.symbol,t])) :
        (data && typeof data === "object" ? data : {});
      let count = 0;
      for (const code of PAIRS) {
        if (batch[code] && valid(Number(batch[code].mid))) {
          accept(batch[code]); count++;
        }
      }
      setMessage(count ? "Prices received" : "Prices unavailable");
    } catch (_) {
      setMessage("Prices unavailable");
      if (!streaming) {
        for (const [code,tick] of quotes) quotes.set(code,{...tick,stale:true});
      }
    } finally { fetching = false; render(); }
  }

  async function connect() {
    try {
      let signalR = window.signalR;
      if (!signalR) {
        const script = document.createElement("script");
        script.src = "https://cdnjs.cloudflare.com/ajax/libs/microsoft-signalr/8.0.0/signalr.min.js";
        script.async = true;
        await new Promise((resolve,reject) => {
          script.onload = resolve; script.onerror = reject; document.head.appendChild(script);
        });
        signalR = window.signalR;
      }
      if (!signalR || disposed) return;
      connection = new signalR.HubConnectionBuilder()
        .withUrl("https://biquote.io/hubs/tick")
        .withAutomaticReconnect()
        .build();
      connection.on("ReceiveTick",tick => { accept(tick); });
      connection.onreconnecting(() => { streaming = false; });
      connection.onreconnected(async () => {
        if (disposed) return;
        try { await connection.invoke("Subscribe",PAIRS); streaming = true; }
        catch (_) { streaming = false; }
      });
      connection.onclose(() => { streaming = false; });
      await connection.start();
      if (disposed) { await connection.stop(); return; }
      await connection.invoke("Subscribe",PAIRS);
      streaming = true;
      setMessage("Prices received");
    } catch (_) { streaming = false; } // One-second REST fallback stays active.
  }

  track.addEventListener("click",event => {
    const button = event.target.closest("button[data-symbol],button[data-clone-symbol]");
    if (!button || !track.contains(button)) return;
    const code = button.dataset.symbol || button.dataset.cloneSymbol;
    if (!PAIRS.includes(code)) return;
    // Once a visitor selects a currency, keep the ticker paused until reload.
    track.classList.add("ticker-stopped");
    const selector = document.getElementById("heroPairSelect");
    if (selector) {
      selector.value = code;
      selector.dispatchEvent(new Event("change",{bubbles:true}));
    }
  });

  daily().then(poll);
  connect();
  // REST fallback runs once per second whenever WebSocket streaming is down.
  const interval = setInterval(() => { render(); if (!streaming) poll(); },1000);
  const openInterval = setInterval(daily,20*60*1000);
  const resume = () => { if (!document.hidden) { poll(); daily(); } };
  document.addEventListener("visibilitychange",resume);
  window.addEventListener("pagehide",() => {
    disposed = true;
    clearInterval(interval); clearInterval(openInterval);
    document.removeEventListener("visibilitychange",resume);
    if (connection) connection.stop().catch(() => {});
  },{once:true});
})();
