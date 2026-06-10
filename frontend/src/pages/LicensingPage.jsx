import { useEffect, useState } from 'react'
import API from '../api/client'
export default function LicensingPage(){const [status,setStatus]=useState(null);const [error,setError]=useState('');useEffect(()=>{API.get('/licensing/status/').then(r=>setStatus(r.data)).catch(()=>setError('Could not load license status.'))},[]);return <div><h2>Subscription Licensing</h2>{error?<div className="alert alert-error">{error}</div>:null}<div className="content-card"><pre>{JSON.stringify(status,null,2)}</pre></div></div>}
