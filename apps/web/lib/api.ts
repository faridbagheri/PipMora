export const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export async function api<T=any>(path:string, init:RequestInit={}):Promise<T>{
  const headers:HeadersInit = { ...(init.body ? {'Content-Type':'application/json'}:{}), ...(init.headers||{}) };
  let response:Response;
  try { response=await fetch(`${API}/api${path}`,{...init,headers,credentials:'include',cache:'no-store'}); }
  catch { throw new Error('Cannot reach PipMora API. Check that the backend is running.'); }
  if(!response.ok){let detail='Request failed';try{const data=await response.json();detail=typeof data.detail==='string'?data.detail:JSON.stringify(data.detail||data)}catch{};const e=new Error(detail) as Error&{status:number};e.status=response.status;throw e}
  if(response.status===204)return undefined as T;
  return response.json();
}
export const post=<T=any>(path:string,body:unknown)=>api<T>(path,{method:'POST',body:JSON.stringify(body)});
export const patch=<T=any>(path:string,body:unknown)=>api<T>(path,{method:'PATCH',body:JSON.stringify(body)});
export const currency=(n:number)=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2}).format(n||0);
export const when=(date:string)=>new Date(date).toLocaleString('en-GB',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
