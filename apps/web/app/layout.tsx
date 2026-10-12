import type {Metadata} from 'next';
import './globals.css';
export const metadata:Metadata={title:'PipMora | Understand the Market. Learn from Every Trade.',description:'AI-powered Forex intelligence, paper trading, economic calendar and evidence-based learning. Educational and simulated data only.',icons:{icon:'/favicon.svg'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en" suppressHydrationWarning><body>{children}</body></html>}
