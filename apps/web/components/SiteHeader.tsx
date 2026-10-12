import Link from 'next/link';
import Brand from './Brand';
import ThemeButton from './ThemeButton';

export default function SiteHeader(){
  return <header className="site-header">
    <div className="container nav">
      <Brand/>
      <nav className="nav-links" aria-label="Public navigation">
        <Link href="/live-charts">Live Forex charts</Link>
        <Link href="/market-intelligence">Market intelligence</Link>
        <Link href="/features">Products</Link>
        <Link href="/how-it-works">How it works</Link>
        <Link href="/ai-trading-coach">AI Coach</Link>
        <Link href="/pricing">Pricing</Link>
      </nav>
      <div className="nav-actions">
        <ThemeButton/>
        <Link href="/login" className="link-login">Log in</Link>
        <Link href="/signup" className="btn btn-primary btn-small">Get started ↗</Link>
      </div>
    </div>
  </header>;
}
