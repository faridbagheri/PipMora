/** Social and contact links for PipMora's official footer. */
const channels=[
 {label:'Farid Bagheri on LinkedIn',href:'https://www.linkedin.com/in/farid-bagheri-a67355ba',kind:'linkedin'},
 {label:'Email Farid Bagheri',href:'mailto:Farid.bagheri8989@gmail.com',kind:'email'},
 {label:'Farid Bagheri personal website',href:'https://faridbagheri.github.io/',kind:'website'}
] as const;

export default function SocialLinks(){
 return <nav className="pm-socials" aria-label="Contact and social links">
  {channels.map(channel=><a key={channel.kind} href={channel.href} aria-label={channel.label}
   title={channel.kind==='website'?'Personal website':channel.kind==='email'?'Email':'LinkedIn'}
   target={channel.kind==='email'?undefined:'_blank'}
   rel={channel.kind==='email'?undefined:'noopener noreferrer'}>
   {channel.kind==='linkedin'?<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2.5" y="2.5" width="19" height="19" rx="3"/><path d="M7.5 10v7M7.5 7v.2M11.5 17v-7M11.5 13.1c0-4.3 6-4.3 6 0V17"/></svg>:
    channel.kind==='email'?<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2.5" y="5" width="19" height="14" rx="2"/><path d="m3.5 7 8.5 6 8.5-6"/></svg>:
    <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9.5"/><path d="M2.5 12h19M12 2.5c-5 5-5 14 0 19M12 2.5c5 5 5 14 0 19"/></svg>}
  </a>)}
 </nav>;
}
