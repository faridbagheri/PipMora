import {Suspense} from 'react';import AuthForm from '@/components/AuthForm';
export default function Page(){return <Suspense fallback={<div className="page-loading">Loading…</div>}><AuthForm mode="reset-password"/></Suspense>}
