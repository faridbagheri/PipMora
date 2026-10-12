import Link from 'next/link';
import Image from 'next/image';

/** The same PipMora candlestick wordmark is used in every application header. */
export default function Brand({compact=false}:{compact?:boolean}){
  return <Link href="/" className="brand" aria-label="PipMora home">
    <Image
      src="/pipmora-wordmark.svg?v=20261013"
      alt="PipMora"
      width={compact?165:210}
      height={compact?49:62}
      className="brand-wordmark"
      priority
      unoptimized
    />
  </Link>;
}
