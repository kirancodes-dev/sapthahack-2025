const { useState, useEffect, useMemo } = React;
const { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, LineChart, Line } = Recharts;

const api = {
    post: async (ep, d) => (await fetch(`/api/v1${ep}`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d)})).json(),
    get: async (ep) => (await fetch(`/api/v1${ep}`)).json()
};

const Loader = () => (<div className="flex justify-center items-center h-64"><div className="w-16 h-16 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div></div>);

const Login = ({ setAuth }) => {
    const [role, setRole] = useState('student');
    const [form, setForm] = useState({email:'', password:''});
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        const res = await api.post('/login', {role, ...form});
        setLoading(false);
        if(res.success) setAuth(res);
        else setError('Invalid Credentials');
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4">
            <div className="glass-panel hud-border p-10 w-full max-w-md relative">
                <div className="absolute top-0 left-0 bg-cyan-500 text-black text-xs font-bold px-2 py-1 font-orbitron">SECURE ACCESS</div>
                <h1 className="text-4xl font-orbitron text-white text-center mb-2 neon-text">SAPTHAHACKS</h1>
                <p className="text-center text-cyan-400 font-rajdhani tracking-widest mb-8">IDENTITY VERIFICATION</p>
                <div className="flex gap-2 mb-6">
                    {['student', 'judge', 'admin'].map(r => (
                        <button key={r} onClick={()=>setRole(r)} className={`flex-1 py-2 font-bold font-orbitron text-xs uppercase transition ${role===r ? 'bg-cyan-500 text-black' : 'bg-black/50 text-gray-400 border border-gray-700'}`}>{r}</button>
                    ))}
                </div>
                <form onSubmit={handleSubmit} className="space-y-5">
                    <input className="w-full bg-black/50 border border-cyan-500/30 text-white p-3 focus:outline-none focus:border-cyan-400 font-rajdhani" placeholder={role==='student'?'Team Lead Email':'Username'} onChange={e=>setForm({...form, email:e.target.value})} />
                    <input type="password" className="w-full bg-black/50 border border-cyan-500/30 text-white p-3 focus:outline-none focus:border-cyan-400 font-rajdhani" placeholder="Password" onChange={e=>setForm({...form, password:e.target.value})} />
                    <button disabled={loading} className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-bold py-3 font-orbitron tracking-wider hover:brightness-110 transition">{loading ? 'AUTHENTICATING...' : 'INITIATE SESSION'}</button>
                </form>
                {error && <p className="text-red-500 text-center mt-4 font-rajdhani border border-red-500/30 bg-red-500/10 p-2">{error}</p>}
            </div>
        </div>
    );
};

const AdminDash = ({ logout }) => {
    const [teams, setTeams] = useState([]);
    const [stats, setStats] = useState(null);
    const refresh = async () => {
        const t = await api.get('/teams');
        const s = await api.get('/stats');
        setTeams(t); setStats(s);
    };
    useEffect(() => { refresh(); }, []);
    const handleAction = async (act, id) => { await api.post('/action', {action: act, id}); refresh(); };
    if(!stats) return <Loader />;
    return (
        <div className="p-8 max-w-7xl mx-auto">
            <header className="flex justify-between items-center mb-10">
                <div><h1 className="text-3xl font-orbitron text-white">COMMAND CENTER</h1><p className="text-cyan-500 font-rajdhani">ADMINISTRATOR LEVEL 10</p></div>
                <button onClick={logout} className="border border-red-500 text-red-500 px-6 py-2 font-orbitron hover:bg-red-500 hover:text-white transition">TERMINATE</button>
            </header>
            <div className="grid grid-cols-4 gap-6 mb-10">
                <div className="glass-panel p-6 text-center"><div className="text-4xl font-bold text-white mb-2">{stats.total_teams}</div><div className="text-xs text-gray-400 font-orbitron">TOTAL UNITS</div></div>
                <div className="glass-panel p-6 text-center"><div className="text-4xl font-bold text-green-400 mb-2">{stats.approved}</div><div className="text-xs text-gray-400 font-orbitron">DEPLOYED</div></div>
                <div className="glass-panel p-6 text-center"><div className="text-4xl font-bold text-cyan-400 mb-2">{Math.round(stats.avg_score)}</div><div className="text-xs text-gray-400 font-orbitron">AVG PERFORMANCE</div></div>
                <div className="glass-panel p-6 text-center"><div className="text-4xl font-bold text-purple-400 mb-2">{stats.tracks.length}</div><div className="text-xs text-gray-400 font-orbitron">ACTIVE SECTORS</div></div>
            </div>
            <div className="grid grid-cols-3 gap-8">
                <div className="col-span-2">
                    <div className="glass-panel p-6"><h2 className="text-xl font-orbitron text-white mb-6 border-b border-gray-700 pb-2">UNIT MANAGEMENT</h2><div className="space-y-4 h-96 overflow-y-auto pr-2">{teams.map(t => (<div key={t.id} className="bg-white/5 p-4 flex justify-between items-center border-l-2 border-cyan-500"><div><h3 className="font-bold text-white">{t.name}</h3><p className="text-xs text-gray-400">{t.track} | {t.members.length} Operatives</p></div><div className="flex items-center gap-4"><span className={`text-xs px-2 py-1 ${t.status==='approved'?'bg-green-500/20 text-green-400':'bg-yellow-500/20 text-yellow-400'}`}>{t.status}</span>{t.status==='pending' && (<div className="flex gap-2"><button onClick={()=>handleAction('approve', t.id)} className="text-green-400 text-xs border border-green-400 px-2 py-1 hover:bg-green-400 hover:text-black">ACCEPT</button><button onClick={()=>handleAction('reject', t.id)} className="text-red-400 text-xs border border-red-400 px-2 py-1 hover:bg-red-400 hover:text-black">DENY</button></div>)}</div></div>))}</div></div>
                </div>
                <div><div className="glass-panel p-6 h-full"><h2 className="text-xl font-orbitron text-white mb-6">SECTOR ANALYSIS</h2><ResponsiveContainer width="100%" height={300}><BarChart data={stats.tracks}><XAxis dataKey="track" tick={{fill:'white', fontSize:10}} /><Tooltip contentStyle={{backgroundColor:'#000', borderColor:'#00f3ff'}} /><Bar dataKey="count" fill="#00f3ff" /></BarChart></ResponsiveContainer></div></div>
            </div>
        </div>
    );
};

const StudentDash = ({ user, logout }) => {
    const [data, setData] = useState(user);
    useEffect(() => { const poll = setInterval(async () => { const teams = await api.get('/teams'); const me = teams.find(t => t.id === user.id); if(me) setData(me); }, 3000); return () => clearInterval(poll); }, []);
    return (
        <div className="p-4 md:p-10 max-w-6xl mx-auto">
            <header className="flex justify-between items-center mb-12">
                <div className="flex items-center gap-4"><div className="w-12 h-12 border-2 border-cyan-400 rounded-full flex items-center justify-center text-cyan-400 animate-pulse"><div className="w-8 h-8 bg-cyan-400 rounded-full"></div></div><div><h1 className="text-4xl font-orbitron text-white">{data.name}</h1><p className="text-cyan-500 font-rajdhani tracking-widest">UNIT ID: {data.id}</p></div></div>
                <button onClick={logout} className="text-gray-400 hover:text-white font-orbitron">DISCONNECT</button>
            </header>
            <div className="grid md:grid-cols-2 gap-8">
                <div className="space-y-8">
                    <div className="glass-panel p-8 hud-border relative"><div className="absolute top-2 right-2 text-xs text-gray-500 font-mono">MODULE: STATUS</div><h2 className="text-2xl font-orbitron text-white mb-4">MISSION PARAMETERS</h2><div className="grid grid-cols-2 gap-4"><div className="bg-black/40 p-4 border border-gray-800"><div className="text-xs text-gray-500">TRACK</div><div className="text-lg text-cyan-300 font-bold">{data.track}</div></div><div className="bg-black/40 p-4 border border-gray-800"><div className="text-xs text-gray-500">STATUS</div><div className={`text-lg font-bold ${data.status==='approved'?'text-green-400':'text-yellow-400'}`}>{data.status.toUpperCase()}</div></div></div></div>
                    <div className="glass-panel p-8 hud-border"><h2 className="text-2xl font-orbitron text-white mb-4">OPERATIVES</h2><div className="space-y-2">{data.members.map((m, i) => (<div key={i} className="flex items-center justify-between bg-white/5 p-3 rounded"><span className="font-bold text-white">{m.name}</span><span className="text-xs text-cyan-500 bg-cyan-500/10 px-2 py-1 rounded">{m.role || 'Specialist'}</span></div>))}</div></div>
                </div>
                <div className="glass-panel p-10 flex flex-col items-center justify-center text-center border-2 border-cyan-500/20 shadow-[0_0_50px_rgba(0,243,255,0.1)]"><h3 className="text-cyan-500 font-rajdhani tracking-[0.5em] mb-6">LIVE PERFORMANCE INDEX</h3><div className="relative"><div className="text-9xl font-black font-orbitron text-white neon-text relative z-10">{data.score}</div><div className="absolute inset-0 blur-2xl bg-cyan-500/20 rounded-full"></div></div><div className="mt-8 w-full bg-gray-800 h-2 rounded-full overflow-hidden"><div className="h-full bg-gradient-to-r from-blue-500 to-cyan-400" style={{width: `${data.score}%`}}></div></div></div>
            </div>
        </div>
    );
};

const App = () => {
    const [auth, setAuth] = useState(null);
    if(!auth) return <Login setAuth={setAuth} />;
    if(auth.role === 'admin') return <AdminDash logout={()=>setAuth(null)} />;
    if(auth.role === 'student') return <StudentDash user={auth.data} logout={()=>setAuth(null)} />;
    return <div className="text-white text-center mt-20">JUDGE INTERFACE LOADING... <button onClick={()=>setAuth(null)}>BACK</button></div>;
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
