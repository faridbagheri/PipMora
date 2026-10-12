import Link from 'next/link';
import SiteHeader from '@/components/SiteHeader';
import SiteFooter from '@/components/SiteFooter';
import LiveForexChart from '@/components/LiveForexChart';

const instruments=[
  {symbol:'FX:EURUSD' as const,pair:'EUR/USD',name:'Euro / US Dollar'},
  {symbol:'FX:GBPUSD' as const,pair:'GBP/USD',name:'British Pound / US Dollar'},
  {symbol:'FX:USDJPY' as const,pair:'USD/JPY',name:'US Dollar / Japanese Yen'},
];

export const metadata={
  title:'Live Forex Charts | PipMora',
  description:'Interactive TradingView-powered EUR/USD, GBP/USD and USD/JPY Forex charts. Separate from PipMora demo trading.'
};

export default function LiveChartsPage(){
  return <><SiteHeader/><main className="live-next-page"><div className="container">
    <div className="live-next-intro">
      <div><span className="eyebrow">FOREX MARKET DATA · POWERED BY TRADINGVIEW</span>
        <h1>Live Forex charts</h1>
        <p>Explore real-time currency charts, candlesticks, timeframes and technical indicators. Source data and availability are controlled by TradingView.</p>
      </div>
      <Link href="/app/demo?preview=true" className="btn btn-primary">Try demo trading ↗</Link>
    </div>
    <div className="live-next-notice">Live charts use a third-party Forex feed. PipMora paper-trading quotes and fills are <strong>synthetic simulations</strong>, not derived from these TradingView widgets.</div>
    <div className="live-next-grid">
      {instruments.map((item,i)=><article key={item.symbol} className={'live-next-card '+(i===0?'live-next-feature':'')}>
        <header><div><h2>{item.pair}</h2><p>{item.name}</p></div><span>TRADINGVIEW DATA</span></header>
        <LiveForexChart symbol={item.symbol}/>
      </article>)}
    </div>
    <p className="live-next-footnote">Forex prices and market hours vary across providers; these charts are not broker executable quotes. This page is informational and not investment advice.</p>
  </div></main><SiteFooter/></>;
}
