import type {Metadata} from 'next';
import './globals.css';
import './pipmora-refresh.css';
import './live-charts.css';
export const metadata:Metadata={
  title:'PipMora | Understand the Market. Learn from Every Trade.',
  description:'AI-powered Forex intelligence, paper trading, economic calendar and evidence-based learning. Educational and simulated data only.',
  icons:{icon:'/pipmora-mark.svg?v=2'}
};
export default function RootLayout({children}:{children:React.ReactNode}){
  return <html lang="en" suppressHydrationWarning><body>{children}</body></html>;
}
