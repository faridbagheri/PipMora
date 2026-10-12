/* Rebuild the public TradingView Symbol Overview widget whenever a visitor
 * selects a currency pair. The embedded widget is cross-origin and has no
 * supported external API for reading quote values.
 */
(function () {
  "use strict";
  const PAIRS = Object.freeze({
    EURUSD:"EUR/USD", GBPUSD:"GBP/USD", USDJPY:"USD/JPY",
    USDCHF:"USD/CHF", AUDUSD:"AUD/USD", EURGBP:"EUR/GBP"
  });
  const select = document.getElementById("heroPairSelect");
  const host = document.getElementById("heroLiveWidget");
  const label = document.getElementById("heroPairTitle");
  const link = document.getElementById("heroChartSource");
  if (!select || !host || !label || !link) return;
  function render(code) {
    if (!Object.prototype.hasOwnProperty.call(PAIRS,code)) return;
    const pair = PAIRS[code];
    label.textContent = pair + " · Provider-supplied market price";
    link.href = "https://www.tradingview.com/symbols/" + code + "/";
    link.textContent = pair + " price and history";
    // Removing the previous iframe and script is required for TradingView to
    // initialize the new symbol rather than retaining the earlier iframe.
    host.replaceChildren();
    const outer = document.createElement("div");
    outer.className = "tradingview-widget-container";
    outer.style.cssText = "height:100%;width:100%";
    const content = document.createElement("div");
    content.className = "tradingview-widget-container__widget";
    content.style.cssText = "height:calc(100% - 30px);width:100%";
    outer.appendChild(content);
    const credit = document.createElement("div");
    credit.className = "tradingview-widget-copyright";
    const provider = document.createElement("a");
    provider.href = link.href;
    provider.target = "_blank";
    provider.rel = "noopener nofollow";
    provider.textContent = pair + " price and history";
    credit.appendChild(provider);
    credit.appendChild(document.createTextNode(" by TradingView"));
    outer.appendChild(credit);
    const script = document.createElement("script");
    script.async = true;
    script.type = "text/javascript";
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js";
    script.textContent = JSON.stringify({
      symbols:[[pair,"FX:" + code + "|1D"]],
      width:"100%",height:"100%",autosize:true,locale:"en",
      colorTheme:"light",isTransparent:false,chartType:"area",
      changeMode:"price-and-percent",hideDateRanges:false,
      hideMarketStatus:false,
      dateRanges:["1d|5","1m|30","3m|60","12m|1D","all|1M"]
    });
    script.onerror = () => {
      content.textContent = "Live chart unavailable. Use the TradingView source link below.";
    };
    outer.appendChild(script);
    host.appendChild(outer);
  }
  try {
    const requested = new URLSearchParams(window.location.search).get("pair");
    if (requested && Object.prototype.hasOwnProperty.call(PAIRS,requested)) select.value = requested;
  } catch (_) {}
  select.addEventListener("change", () => {
    render(select.value);
  });
  render(select.value);
})();
