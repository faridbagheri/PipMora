import Link from 'next/link';
import Image from 'next/image';

export default function Brand({compact=false}:{compact?:boolean}){
  return <Link href="/" className="brand" aria-label="PipMora home">
    <Image src="/pipmora-mark.svg?v=2" alt="" width={43} height={43} className="brand-mark" />
    {!compact&&<span>PipMora</span>}
  </Link>;
}
