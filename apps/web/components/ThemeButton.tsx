'use client';
import {useEffect,useState} from 'react';
export default function ThemeButton(){
  const [theme,setTheme]=useState<'light'|'dark'>('light');
  useEffect(()=>{
    const stored=localStorage.getItem('pipmora-theme');
    const next=stored==='dark'?'dark':'light';
    setTheme(next);document.documentElement.setAttribute('data-theme',next);
  },[]);
  return <button className="theme-button" aria-label="Toggle theme" title="Toggle dark or light mode"
    onClick={()=>{
      const next=theme==='dark'?'light':'dark';
      setTheme(next);document.documentElement.setAttribute('data-theme',next);localStorage.setItem('pipmora-theme',next);
    }}>{theme==='dark'?'☀':'☾'}</button>;
}
