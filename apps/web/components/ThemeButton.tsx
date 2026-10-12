'use client';
import {useEffect,useState} from 'react';
export default function ThemeButton(){const[theme,setTheme]=useState('dark');useEffect(()=>{const x=localStorage.getItem('pipmora-theme')||'dark';setTheme(x);document.documentElement.setAttribute('data-theme',x)},[]);return <button className="theme-button" aria-label="Toggle theme" title="Toggle dark or light mode" onClick={()=>{const n=theme==='dark'?'light':'dark';setTheme(n);document.documentElement.setAttribute('data-theme',n);localStorage.setItem('pipmora-theme',n)}}>{theme==='dark'?'☼':'☾'}</button>}
