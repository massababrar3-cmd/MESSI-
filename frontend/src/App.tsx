import { useEffect, useState, type ReactNode } from 'react';
import {
  Box,
  Layers3,
  CalendarDays,
  Truck,
  Mountain,
  GitBranch,
  FileBarChart,
  Users,
  History,
  ChevronDown,
  Plus,
  Upload,
  Play,
  ArrowUpRight,
  Check,
  CheckCircle2,
  AlertTriangle,
  LogOut,
  X,
  Save,
  Copy,
  ShieldCheck,
  ArrowRight,
  Clock,
  SlidersHorizontal,
  Download,
  LoaderCircle,
  LockKeyhole,
  Pickaxe,
  Database,
} from 'lucide-react';
import { api, post, setCSRF, number } from './api';
import type { User, Project, Scenario, Inputs, Block, Run } from './types';
import Viewer from './Viewer';

type Tab = 'planning' | 'equipment' | 'materials' | 'scenarios' | 'reports' | 'team' | 'audit';
const EMPTY_SURFACES: import('./types').Surface[] = [];
const NAV: { id: Tab; label: string; icon: typeof Box }[] = [
  { id: 'planning', label: 'Planning studio', icon: Layers3 },
  { id: 'equipment', label: 'Fleet & calendars', icon: Truck },
  { id: 'materials', label: 'Material balance', icon: Mountain },
  { id: 'scenarios', label: 'Scenarios', icon: GitBranch },
  { id: 'reports', label: 'Reports & exports', icon: FileBarChart },
  { id: 'team', label: 'Project team', icon: Users },
  { id: 'audit', label: 'Activity log', icon: History },
];
function Modal({
  title,
  children,
  close,
}: {
  title: string;
  children: ReactNode;
  close: () => void;
}) {
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <section className="modal" role="dialog" aria-modal="true" aria-label={title}>
        <header>
          <h2>{title}</h2>
          <button aria-label="Close dialog" onClick={close}>
            <X size={20} />
          </button>
        </header>
        {children}
      </section>
    </div>
  );
}
function Badge({ status }: { status: string }) {
  return (
    <span
      className={`badge ${['feasible', 'approved'].includes(status) ? 'good' : ['running', 'queued'].includes(status) ? 'blue' : ['partial', 'stale'].includes(status) ? 'warn' : ''}`}
    >
      <i />
      {status.replaceAll('_', ' ')}
    </span>
  );
}
function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [email, setEmail] = useState(''),
    [password, setPassword] = useState(''),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false);
  return (
    <div className="login-page">
      <div className="login-story">
        <div className="brand">
          <span className="brand-icon">
            <Mountain />
          </span>
          <strong>
            MESSI<span> MINE PLANNING STUDIO</span>
          </strong>
        </div>
        <div className="login-grid" />
        <div className="login-copy">
          <span className="eyebrow">ENGINEER THE NEXT MOVE</span>
          <h1>
            See the mine.
            <br />
            Shape the plan.
          </h1>
          <p>
            One workspace for your coal model, equipment and production schedule. Built around
            traceable engineering decisions.
          </p>
          <div className="login-pills">
            <span>
              <Box size={15} />
              3D modelling
            </span>
            <span>
              <CalendarDays size={15} />
              Production planning
            </span>
            <span>
              <Users size={15} />
              Team workspace
            </span>
          </div>
        </div>
        <small>Independent mine planning · Open-cut coal · Development pilot</small>
      </div>
      <div className="login-form">
        <span className="eyebrow">YOUR PLANNING WORKSPACE</span>
        <h2>Welcome to MESSI</h2>
        <p>Sign in to open your projects and production plans.</p>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError('');
            try {
              const r = await post('/auth/login', { email, password });
              setCSRF(r.csrf);
              onLogin(r.user);
            } catch (e) {
              setError(String((e as Error).message));
            } finally {
              setBusy(false);
            }
          }}
        >
          <label>
            Email address
            <input
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {error && (
            <div className="notice error" role="alert">
              {error}
            </div>
          )}
          <button className="primary" disabled={busy}>
            {busy ? <LoaderCircle className="spin" size={17} /> : null}Sign in
            <ArrowRight size={17} />
          </button>
        </form>
        <div className="login-note">
          <ShieldCheck size={19} />
          <p>
            Project permissions are enforced on the server. Local pilot credentials are stored
            privately in <code>.local/bootstrap-users.json</code>.
          </p>
        </div>
      </div>
    </div>
  );
}
export default function App() {
  const [user, setUser] = useState<User | null | undefined>(undefined),
    [projects, setProjects] = useState<Project[]>([]),
    [projectId, setProjectId] = useState(''),
    [scenarios, setScenarios] = useState<Scenario[]>([]),
    [scenario, setScenario] = useState<Scenario | null>(null),
    [inputs, setInputs] = useState<Inputs | null>(null),
    [dirty, setDirty] = useState(false),
    [selected, setSelected] = useState<string | null>(null),
    [run, setRun] = useState<Run | null>(null),
    [runs, setRuns] = useState<Run[]>([]),
    [viewRun, setViewRun] = useState(''),
    [tab, setTab] = useState<Tab>('planning'),
    [modal, setModal] = useState(''),
    [error, setError] = useState(''),
    [success, setSuccess] = useState(''),
    [busy, setBusy] = useState(false),
    [playDate, setPlayDate] = useState(''),
    [filter, setFilter] = useState('all');
  const [branchName, setBranchName] = useState(''),
    [newName, setNewName] = useState(''),
    [newCRS, setNewCRS] = useState('Local engineering grid (metres)'),
    [newDatum, setNewDatum] = useState('Site RL (metres)'),
    [useSample, setUseSample] = useState(false);
  const [importKind, setImportKind] = useState('blocks');
  const [csvText, setCsvText] = useState(''),
    [csvUnits, setCsvUnits] = useState('m'),
    [preview, setPreview] = useState<any>(null),
    [fileName, setFileName] = useState(''),
    [members, setMembers] = useState<any[]>([]),
    [audit, setAudit] = useState<any[]>([]),
    [memberEmail, setMemberEmail] = useState(''),
    [memberRole, setMemberRole] = useState('viewer');
  function clearSession() {
    setCSRF('');
    setUser(null);
    setProjects([]);
    setProjectId('');
    setScenarios([]);
    setScenario(null);
    setInputs(null);
    setRun(null);
    setRuns([]);
    setDirty(false);
    setModal('');
    setError('');
    setSuccess('');
  }
  useEffect(() => {
    window.addEventListener('messi-session-expired', clearSession);
    return () => window.removeEventListener('messi-session-expired', clearSession);
  }, []);
  const project = projects.find((p) => p.id === projectId);
  const canEdit = project?.role === 'owner' || project?.role === 'planner';
  const canApprove = project?.role === 'owner' || project?.role === 'reviewer';
  const block = inputs?.blocks.find((b) => b.id === selected);
  const stale = !!run && !!scenario && (run.revision !== scenario.revision || dirty);
  const active = run && ['queued', 'running'].includes(run.status);
  async function loadProjects() {
    const data = await api<Project[]>('/projects');
    setProjects(data);
    setProjectId((p) => (data.some((x) => x.id === p) ? p : data[0]?.id || ''));
  }
  useEffect(() => {
    api('/auth/me')
      .then((r) => {
        setCSRF(r.csrf);
        setUser(r.user);
      })
      .catch(() => setUser(null));
  }, []);
  useEffect(() => {
    if (user) loadProjects().catch((e) => setError(e.message));
  }, [user?.id]);
  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    setScenario(null);
    setInputs(null);
    setRun(null);
    setViewRun('');
    setDirty(false);
    api<Scenario[]>(`/projects/${projectId}/scenarios`)
      .then((data) => {
        if (!cancelled) {
          setScenarios(data);
          chooseScenario(data[0]);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);
  function chooseScenario(s: Scenario | undefined) {
    if (!s) return;
    setScenario(s);
    setInputs(structuredClone(s.inputs));
    setSelected(s.inputs.blocks[0]?.id || null);
    setDirty(false);
    setRun(null);
    setViewRun('');
    setPlayDate('');
  }
  useEffect(() => {
    if (!projectId || !scenario) return;
    let cancelled = false;
    async function poll() {
      try {
        const list = await api<Run[]>(`/projects/${projectId}/runs`);
        if (cancelled) return;
        setRuns(list);
        const chosen =
          list.find((r) => r.id === viewRun && r.scenario_id === scenario!.id) ||
          list.find((r) => r.scenario_id === scenario!.id);
        if (chosen) {
          const full = await api<Run>(`/runs/${chosen.id}`);
          if (!cancelled) setRun(full);
        } else setRun(null);
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      }
    }
    poll();
    const timer = setInterval(poll, 1800);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [projectId, scenario?.id, viewRun]);
  useEffect(() => {
    if (tab === 'team' && projectId)
      api<any[]>(`/projects/${projectId}/members`)
        .then(setMembers)
        .catch((e) => setError(e.message));
    if (tab === 'audit' && projectId)
      api<any[]>(`/projects/${projectId}/audit`)
        .then(setAudit)
        .catch((e) => setError(e.message));
  }, [tab, projectId, success]);
  async function perform(fn: () => Promise<void>) {
    setBusy(true);
    setError('');
    setSuccess('');
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function edit(next: Inputs) {
    setInputs(next);
    setDirty(true);
  }
  function editBlock(patch: Partial<Block>) {
    if (inputs && block)
      edit({
        ...inputs,
        blocks: inputs.blocks.map((b) => (b.id === block.id ? { ...b, ...patch } : b)),
      });
  }
  async function save() {
    if (!scenario || !inputs) throw new Error('No scenario selected');
    const saved = await api<Scenario>(`/scenarios/${scenario.id}`, {
      method: 'PUT',
      body: JSON.stringify({ revision: scenario.revision, inputs }),
    });
    setScenario(saved);
    setInputs(structuredClone(saved.inputs));
    setScenarios((list) => list.map((s) => (s.id === saved.id ? saved : s)));
    setDirty(false);
    return saved;
  }
  async function startRun() {
    const s = dirty ? await save() : scenario;
    if (!s) return;
    const next = await post<Run>(`/scenarios/${s.id}/runs`, {
      revision: s.revision,
      idempotency_key: crypto.randomUUID(),
    });
    setRun(next);
    setViewRun(next.id);
    setSuccess('Schedule submitted. You can keep working while the server runs it.');
  }
  const confirmDiscard = () => !dirty || window.confirm('Discard unsaved scenario changes?');
  if (user === undefined)
    return (
      <div className="app-loading">
        <Mountain size={40} />
        <span>Opening MESSI…</span>
      </div>
    );
  if (!user) return <Login onLogin={setUser} />;
  const totalVolume = inputs?.blocks.reduce((n, b) => n + b.dx * b.dy * b.dz, 0) || 0;
  const coal =
    inputs?.blocks
      .filter((b) => b.material === 'coal')
      .reduce((n, b) => n + b.dx * b.dy * b.dz * b.density, 0) || 0;
  const waste =
    inputs?.blocks
      .filter((b) => b.material === 'waste')
      .reduce((n, b) => n + b.dx * b.dy * b.dz * b.density, 0) || 0;
  const onSelectScenario = (id: string) => {
    if (confirmDiscard()) chooseScenario(scenarios.find((s) => s.id === id));
  };
  return (
    <div className="application">
      <aside className="sidebar">
        <a className="brand" href="#">
          <span className="brand-icon">
            <Mountain size={24} />
          </span>
          <strong>
            MESSI<span>MINE PLANNING STUDIO</span>
          </strong>
        </a>
        <div className="workspace-label">WORKSPACE</div>
        <div className="project-picker">
          <Database size={18} />
          <select
            aria-label="Project"
            value={projectId}
            onChange={(e) => {
              if (confirmDiscard()) setProjectId(e.target.value);
            }}
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
            {!projects.length && <option>No projects</option>}
          </select>
          <ChevronDown size={14} />
        </div>
        <button
          className="new-project"
          onClick={() => {
            setNewName('');
            setModal('project');
          }}
        >
          <Plus size={14} />
          New project
        </button>
        <div className="workspace-label">PLANNING</div>
        <nav>
          {NAV.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              aria-label={label}
              className={tab === id ? 'selected' : ''}
              onClick={() => setTab(id)}
            >
              <Icon size={18} />
              <span>{label}</span>
              {id === 'scenarios' && <small>{scenarios.length}</small>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="pilot-note">
            <span className="live-dot" />
            <b>Engineering pilot</b>
            <p>Baseline scheduling. Site validation required before operational use.</p>
          </div>
          <div className="user-card">
            <span className="avatar">
              {user.name
                .split(' ')
                .map((x) => x[0])
                .slice(0, 2)
                .join('')}
            </span>
            <div>
              <b>{user.name}</b>
              <small>{project?.role || 'User'}</small>
            </div>
            <button
              title="Sign out"
              aria-label="Sign out"
              onClick={() =>
                perform(async () => {
                  await post('/auth/logout');
                  clearSession();
                })
              }
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> {project?.name || 'Projects'} <span>/</span>
            <strong>{NAV.find((n) => n.id === tab)?.label}</strong>
          </div>
          <div className="top-meta">
            <span className="live-dot" />
            Server workspace<span className="version">v0.1</span>
          </div>
        </header>
        <main>
          <div className="page-header">
            <div>
              <div className="eyebrow">OPEN-CUT COAL PLANNING</div>
              <h1>{NAV.find((n) => n.id === tab)?.label}</h1>
              <p>
                {tab === 'planning'
                  ? 'From a physical model to your next feasible production plan.'
                  : tab === 'equipment'
                    ? 'Define working capacity, maintenance and the planning calendar.'
                    : tab === 'materials'
                      ? 'Follow every tonne from mining block to destination.'
                      : tab === 'scenarios'
                        ? 'Explore alternatives while preserving your original baseline.'
                        : tab === 'reports'
                          ? 'Share reconciled quantities with their assumptions and provenance.'
                          : tab === 'team'
                            ? 'Control project access and review responsibilities.'
                            : 'A traceable record of project decisions and changes.'}
              </p>
            </div>
            <div className="header-actions">
              {dirty && canEdit && (
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() =>
                    perform(async () => {
                      await save();
                      setSuccess('Scenario changes saved. Run a new schedule to refresh results.');
                    })
                  }
                >
                  <Save size={16} />
                  Save changes
                </button>
              )}
              {canEdit && (
                <button
                  className="secondary"
                  onClick={() => {
                    setPreview(null);
                    setFileName('');
                    setCsvText('');
                    setModal('import');
                  }}
                >
                  <Upload size={16} />
                  Import model
                </button>
              )}
              {canEdit && (
                <button
                  className="primary"
                  disabled={busy || !!active || !inputs?.blocks.length}
                  onClick={() => perform(startRun)}
                >
                  {active ? <LoaderCircle size={17} className="spin" /> : <Play size={16} />}{' '}
                  {active ? 'Scheduling…' : 'Run schedule'}
                </button>
              )}
            </div>
          </div>
          {error && (
            <div className="notice error" role="alert">
              <AlertTriangle size={17} />
              <span>{error}</span>
              <button aria-label="Dismiss error" onClick={() => setError('')}>
                <X size={16} />
              </button>
            </div>
          )}
          {success && (
            <div className="notice success" role="status">
              <CheckCircle2 size={17} />
              <span>{success}</span>
              <button aria-label="Dismiss notification" onClick={() => setSuccess('')}>
                <X size={16} />
              </button>
            </div>
          )}
          {!projects.length ? (
            <section className="empty-state">
              <Mountain size={50} />
              <h2>Your first mine plan starts here</h2>
              <p>Create a project, declare its reference system and import your blocks.</p>
              <button className="primary" onClick={() => setModal('project')}>
                <Plus size={17} />
                Create project
              </button>
            </section>
          ) : !inputs || !scenario ? (
            <div className="loading-inline">
              <LoaderCircle className="spin" />
              Loading project…
            </div>
          ) : (
            <>
              <div className="scenario-strip">
                <div>
                  <GitBranch size={16} />
                  <select
                    aria-label="Scenario"
                    value={scenario.id}
                    onChange={(e) => onSelectScenario(e.target.value)}
                  >
                    {scenarios.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                  <span className="revision">REV {scenario.revision}</span>
                  {dirty && <span className="unsaved">Unsaved changes</span>}
                </div>
                <div>
                  <CalendarDays size={15} />
                  <span>
                    {inputs.calendar.start} · {inputs.calendar.days} days
                  </span>
                  <span className="divider" />
                  {inputs.source.kind === 'synthetic' ? (
                    <span className="synthetic">Synthetic pilot data</span>
                  ) : (
                    <span>Imported engineering model</span>
                  )}
                </div>
              </div>
              {stale && (
                <div className="notice warning">
                  <AlertTriangle size={16} />
                  Inputs changed. The displayed run is revision {run?.revision}; rerun before using
                  results for the current scenario.
                </div>
              )}
              {tab === 'planning' && (
                <>
                  <div className="metrics">
                    <Metric
                      label="IN-SITU VOLUME"
                      value={number(totalVolume)}
                      unit="m³"
                      icon={<Box />}
                      sub={`${inputs.blocks.length} planning blocks · declared geometry`}
                    />
                    <Metric
                      label="MODEL COAL"
                      value={number(coal)}
                      unit="t"
                      icon={<Pickaxe />}
                      sub="Quantity basis shown per material"
                      accent="teal"
                    />
                    <Metric
                      label="MODEL WASTE"
                      value={number(waste)}
                      unit="t"
                      icon={<Mountain />}
                      sub={`${coal ? number(waste / coal, 2) : '—'} t waste / t coal · mass ratio`}
                      accent="sand"
                    />
                    <Metric
                      label="SCHEDULE STATUS"
                      value={
                        active
                          ? `${run!.progress}%`
                          : run?.result
                            ? `${run.result.activities.filter((a) => a.complete).length} / ${run.snapshot?.blocks.length ?? inputs.blocks.length}`
                            : 'Not run'
                      }
                      unit={run?.result ? 'blocks' : ''}
                      icon={<CalendarDays />}
                      sub={
                        run?.result
                          ? `${run.result.violations.length} validation violations · ${run.status}`
                          : 'Configure constraints, then run'
                      }
                      accent="blue"
                    />
                  </div>
                  <div className="planning-grid">
                    <section className="panel model-panel">
                      <Viewer
                        blocks={inputs.blocks}
                        surfaces={inputs.surfaces || EMPTY_SURFACES}
                        selected={selected}
                        onSelect={setSelected}
                        run={stale ? null : run}
                        date={playDate}
                      />
                      <div className="model-footer">
                        <span>
                          <span className="live-dot" />
                          {project?.crs}
                        </span>
                        <span>
                          {project?.datum} · {inputs.blocks.length} blocks
                        </span>
                      </div>
                    </section>
                    <aside className="panel inspector">
                      <div className="panel-title">
                        <h2>Block inspector</h2>
                        <SlidersHorizontal size={16} />
                      </div>
                      {block ? (
                        <>
                          <div className="block-heading">
                            <span className={`material-icon ${block.material}`}>
                              <Box size={22} />
                            </span>
                            <div>
                              <h3>{block.id}</h3>
                              <span>
                                {block.material === 'coal' ? 'Coal seam' : 'Overburden'} ·{' '}
                                {block.basis.replace('_', ' ')} basis
                              </span>
                            </div>
                          </div>
                          <div className="property-grid">
                            <div>
                              <small>VOLUME</small>
                              <b>
                                {number(block.dx * block.dy * block.dz)} <em>m³</em>
                              </b>
                            </div>
                            <div>
                              <small>TONNAGE</small>
                              <b>
                                {number(block.dx * block.dy * block.dz * block.density)} <em>t</em>
                              </b>
                            </div>
                          </div>
                          <div className="inspector-form">
                            <label>
                              Priority
                              <input
                                aria-label="Block priority"
                                type="number"
                                min="0"
                                max="10000"
                                disabled={!canEdit}
                                value={block.priority}
                                onChange={(e) => editBlock({ priority: +e.target.value })}
                              />
                            </label>
                            <label>
                              Destination
                              <select
                                disabled={!canEdit}
                                value={block.destination}
                                onChange={(e) => editBlock({ destination: e.target.value })}
                              >
                                {inputs.destinations
                                  .filter(
                                    (d) => d.material === block.material && d.basis === block.basis,
                                  )
                                  .map((d) => (
                                    <option value={d.id} key={d.id}>
                                      {d.name}
                                    </option>
                                  ))}
                              </select>
                            </label>
                            <label>
                              Predecessors <small>IDs separated by ;</small>
                              <input
                                aria-label="Block predecessors"
                                disabled={!canEdit}
                                value={block.predecessors.join(';')}
                                onChange={(e) =>
                                  editBlock({
                                    predecessors: e.target.value
                                      .split(';')
                                      .map((v) => v.trim())
                                      .filter(Boolean),
                                  })
                                }
                              />
                            </label>
                            <label>
                              Locked start date
                              <input
                                aria-label="Locked start date"
                                type="date"
                                disabled={!canEdit}
                                value={block.locked_start?.slice(0, 10) || ''}
                                onChange={(e) =>
                                  editBlock({ locked_start: e.target.value || null })
                                }
                              />
                            </label>
                            <label>
                              Resource lock
                              <select
                                disabled={!canEdit}
                                value={block.locked_resource || ''}
                                onChange={(e) =>
                                  editBlock({ locked_resource: e.target.value || null })
                                }
                              >
                                <option value="">Automatic allocation</option>
                                {inputs.resources
                                  .filter((r) => r.materials.includes(block.material))
                                  .map((r) => (
                                    <option value={r.id} key={r.id}>
                                      {r.name}
                                    </option>
                                  ))}
                              </select>
                            </label>
                            <details>
                              <summary>Geometry & quality</summary>
                              <div className="mini-fields">
                                {(['x', 'y', 'z', 'dx', 'dy', 'dz', 'density'] as const).map(
                                  (k) => (
                                    <label key={k}>
                                      {k}
                                      {k === 'density' ? ' (t/m³)' : ' (m)'}
                                      <input
                                        type="number"
                                        step="any"
                                        disabled={!canEdit}
                                        aria-label={`Block ${k}`}
                                        value={block[k]}
                                        onChange={(e) => editBlock({ [k]: +e.target.value })}
                                      />
                                    </label>
                                  ),
                                )}
                                {block.material === 'coal' && (
                                  <label>
                                    Ash % ({block.basis})
                                    <input
                                      type="number"
                                      disabled={!canEdit}
                                      step="0.1"
                                      value={block.ash ?? ''}
                                      onChange={(e) => editBlock({ ash: +e.target.value })}
                                    />
                                  </label>
                                )}
                              </div>
                            </details>
                          </div>
                        </>
                      ) : (
                        <div className="empty-small">
                          Select a block in the model or table to inspect it.
                        </div>
                      )}
                    </aside>
                  </div>
                  <section className="panel schedule-panel">
                    <div className="panel-title">
                      <div>
                        <h2>Production schedule</h2>
                        <span>Deterministic baseline · {inputs.timezone}</span>
                      </div>
                      <div className="row">
                        {run && <Badge status={run.status} />}
                        <select
                          aria-label="Displayed schedule run"
                          value={viewRun || run?.id || ''}
                          onChange={(e) => setViewRun(e.target.value)}
                        >
                          <option value="">Latest run</option>
                          {runs
                            .filter((r) => r.scenario_id === scenario.id)
                            .map((r) => (
                              <option key={r.id} value={r.id}>
                                Rev {r.revision} · {r.created.slice(11, 19)} · {r.status}
                              </option>
                            ))}
                        </select>
                      </div>
                    </div>
                    {active ? (
                      <div className="job-progress">
                        <LoaderCircle className="spin" />
                        <div>
                          <b>Building a feasible plan</b>
                          <p>
                            The server checks precedence, shifts, resources and destination limits.
                          </p>
                          <progress value={run!.progress} max={100} />
                        </div>
                        {canEdit && (
                          <button
                            className="secondary"
                            onClick={() =>
                              perform(async () => {
                                await post(`/runs/${run!.id}/cancel`);
                                setSuccess('Cancellation requested.');
                              })
                            }
                          >
                            Cancel job
                          </button>
                        )}
                      </div>
                    ) : run?.result ? (
                      <>
                        <Gantt
                          run={run}
                          inputs={run.snapshot || inputs}
                          selected={selected}
                          select={setSelected}
                        />
                        <div className="playback">
                          <Play size={15} />
                          <label>
                            3D extraction playback
                            <input
                              aria-label="Playback date"
                              type="date"
                              min={inputs.calendar.start}
                              value={playDate}
                              onChange={(e) => setPlayDate(e.target.value)}
                            />
                          </label>
                          <button onClick={() => setPlayDate('')}>Reset</button>
                          <span>Completed blocks darken · {playDate || 'full model'}</span>
                        </div>
                        {run.result.unscheduled.length > 0 && (
                          <div className="conflicts">
                            <b>{run.result.unscheduled.length} unscheduled blocks</b>
                            {run.result.unscheduled.map((u) => (
                              <p key={u.id}>
                                <strong>{u.id}</strong> {u.reason}
                              </p>
                            ))}
                          </div>
                        )}
                        {run.result.violations.map((v, i) => (
                          <div className="notice error" key={i}>
                            {v}
                          </div>
                        ))}
                      </>
                    ) : (
                      <div className="empty-small">
                        <CalendarDays size={27} />
                        <b>No schedule yet</b>
                        <span>Review your fleet and dependencies, then run the schedule.</span>
                        {run?.error && <p>{run.error}</p>}
                      </div>
                    )}
                  </section>
                  <section className="panel">
                    <div className="panel-title">
                      <h2>
                        Planning blocks <span className="count">{inputs.blocks.length}</span>
                      </h2>
                      <select
                        aria-label="Filter material"
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                      >
                        <option value="all">All materials</option>
                        <option value="coal">Coal</option>
                        <option value="waste">Waste</option>
                      </select>
                    </div>
                    <div className="table-scroll">
                      <table>
                        <thead>
                          <tr>
                            <th>BLOCK ID</th>
                            <th>MATERIAL</th>
                            <th>VOLUME m³</th>
                            <th>TONNES t</th>
                            <th>DENSITY t/m³</th>
                            <th>PREDECESSORS</th>
                            <th>PRIORITY</th>
                          </tr>
                        </thead>
                        <tbody>
                          {inputs.blocks
                            .filter((b) => filter === 'all' || b.material === filter)
                            .map((b) => (
                              <tr
                                key={b.id}
                                className={b.id === selected ? 'active-row' : ''}
                                onClick={() => setSelected(b.id)}
                              >
                                <td>
                                  <button className="table-link" onClick={() => setSelected(b.id)}>
                                    {b.id}
                                  </button>
                                </td>
                                <td>
                                  <span className={`material-label ${b.material}`}>
                                    <i />
                                    {b.material}
                                  </span>
                                </td>
                                <td>{number(b.dx * b.dy * b.dz)}</td>
                                <td>{number(b.dx * b.dy * b.dz * b.density)}</td>
                                <td>{number(b.density, 3)}</td>
                                <td>{b.predecessors.join(', ') || '—'}</td>
                                <td>{b.priority}</td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>
                  </section>
                </>
              )}
              {tab === 'equipment' && (
                <>
                  <section className="panel">
                    <div className="panel-title">
                      <div>
                        <h2>Equipment & production rates</h2>
                        <span>
                          Tonnes per working hour · utilization applied once; maintenance removes
                          calendar hours.
                        </span>
                      </div>
                      {canEdit && (
                        <button
                          className="secondary"
                          onClick={() =>
                            edit({
                              ...inputs,
                              resources: [
                                ...inputs.resources,
                                {
                                  id: `fleet-${crypto.randomUUID().slice(0, 8)}`,
                                  name: 'New mining fleet',
                                  rate: 1000,
                                  utilization: 1,
                                  materials: ['coal', 'waste'],
                                  outages: [],
                                },
                              ],
                            })
                          }
                        >
                          <Plus size={16} />
                          Add fleet
                        </button>
                      )}
                    </div>
                    <div className="resource-grid">
                      {inputs.resources.map((r, i) => (
                        <div className="resource-card" key={r.id}>
                          <div className="resource-icon">
                            <Truck size={26} />
                            <span>EXCLUSIVE RESOURCE</span>
                          </div>
                          <label>
                            Fleet name
                            <input
                              disabled={!canEdit}
                              value={r.name}
                              onChange={(e) =>
                                edit({
                                  ...inputs,
                                  resources: inputs.resources.map((x, j) =>
                                    j === i ? { ...x, name: e.target.value } : x,
                                  ),
                                })
                              }
                            />
                          </label>
                          <div className="form-grid">
                            <label>
                              Rate (t/h)
                              <input
                                aria-label={`Rate ${r.id}`}
                                type="number"
                                min="1"
                                disabled={!canEdit}
                                value={r.rate}
                                onChange={(e) =>
                                  edit({
                                    ...inputs,
                                    resources: inputs.resources.map((x, j) =>
                                      j === i ? { ...x, rate: +e.target.value } : x,
                                    ),
                                  })
                                }
                              />
                            </label>
                            <label>
                              Utilization (%)
                              <input
                                type="number"
                                min="1"
                                max="100"
                                disabled={!canEdit}
                                value={Math.round(r.utilization * 100)}
                                onChange={(e) =>
                                  edit({
                                    ...inputs,
                                    resources: inputs.resources.map((x, j) =>
                                      j === i ? { ...x, utilization: +e.target.value / 100 } : x,
                                    ),
                                  })
                                }
                              />
                            </label>
                          </div>
                          <div className="row">
                            {(['coal', 'waste'] as const).map((m) => (
                              <label className="checkbox" key={m}>
                                <input
                                  type="checkbox"
                                  disabled={!canEdit}
                                  checked={r.materials.includes(m)}
                                  onChange={(e) =>
                                    edit({
                                      ...inputs,
                                      resources: inputs.resources.map((x, j) =>
                                        j === i
                                          ? {
                                              ...x,
                                              materials: e.target.checked
                                                ? [...x.materials, m]
                                                : x.materials.filter((a) => a !== m),
                                            }
                                          : x,
                                      ),
                                    })
                                  }
                                />
                                {m}
                              </label>
                            ))}
                          </div>
                          <label>
                            Maintenance dates (YYYY-MM-DD; one per line)
                            <textarea
                              disabled={!canEdit}
                              value={r.outages.join('\n')}
                              onChange={(e) =>
                                edit({
                                  ...inputs,
                                  resources: inputs.resources.map((x, j) =>
                                    j === i
                                      ? {
                                          ...x,
                                          outages: e.target.value.split('\n').filter(Boolean),
                                        }
                                      : x,
                                  ),
                                })
                              }
                            />
                          </label>
                          <div className="capacity">
                            {number(r.rate * r.utilization * inputs.calendar.shift_hours)}{' '}
                            <span>t per available shift</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                  <section className="panel calendar-panel">
                    <div className="panel-title">
                      <h2>Planning calendar</h2>
                      <span>{inputs.timezone}</span>
                    </div>
                    <div className="form-grid four">
                      {(['start', 'days', 'shift_start', 'shift_hours'] as const).map((k) => (
                        <label key={k}>
                          {
                            {
                              start: 'Horizon start',
                              days: 'Horizon (days)',
                              shift_start: 'Shift start (0–23)',
                              shift_hours: 'Shift hours',
                            }[k]
                          }
                          <input
                            type={k === 'start' ? 'date' : 'number'}
                            disabled={!canEdit}
                            value={inputs.calendar[k]}
                            onChange={(e) =>
                              edit({
                                ...inputs,
                                calendar: {
                                  ...inputs.calendar,
                                  [k]: k === 'start' ? e.target.value : +e.target.value,
                                },
                              })
                            }
                          />
                        </label>
                      ))}
                    </div>
                    <div className="weekdays">
                      {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d, i) => (
                        <button
                          key={d}
                          disabled={!canEdit}
                          className={inputs.calendar.weekdays.includes(i) ? 'active' : ''}
                          onClick={() =>
                            edit({
                              ...inputs,
                              calendar: {
                                ...inputs.calendar,
                                weekdays: inputs.calendar.weekdays.includes(i)
                                  ? inputs.calendar.weekdays.filter((v) => v !== i)
                                  : [...inputs.calendar.weekdays, i],
                              },
                            })
                          }
                        >
                          {d}
                        </button>
                      ))}
                    </div>
                    <p className="muted">
                      Same-day shifts, splittable activities, no overtime. Overnight shift patterns
                      are not supported in this release.
                    </p>
                  </section>
                </>
              )}
              {tab === 'materials' && (
                <>
                  <div className="section-intro">
                    <h2>Destinations & stock balance</h2>
                    <p>
                      Perfectly mixed stocks. Receipts from mining only; reclaim and processing are
                      not modelled in this release.
                    </p>
                  </div>
                  <div className="destination-grid">
                    {inputs.destinations.map((d, i) => {
                      const stock = run?.result?.stocks.find((s) => s.id === d.id);
                      return (
                        <section className="panel destination-card" key={d.id}>
                          <div className="row between">
                            <span className={`material-label ${d.material}`}>
                              <i />
                              {d.material} · {d.basis.replace('_', ' ')}
                            </span>
                            <Mountain size={22} />
                          </div>
                          <h2>{d.name}</h2>
                          <label>
                            Capacity (t)
                            <input
                              type="number"
                              disabled={!canEdit}
                              value={d.capacity}
                              onChange={(e) =>
                                edit({
                                  ...inputs,
                                  destinations: inputs.destinations.map((x, j) =>
                                    i === j ? { ...x, capacity: +e.target.value } : x,
                                  ),
                                })
                              }
                            />
                          </label>
                          <label>
                            Opening stock (t)
                            <input
                              type="number"
                              disabled={!canEdit}
                              value={d.opening}
                              onChange={(e) =>
                                edit({
                                  ...inputs,
                                  destinations: inputs.destinations.map((x, j) =>
                                    i === j ? { ...x, opening: +e.target.value } : x,
                                  ),
                                })
                              }
                            />
                          </label>
                          {d.material === 'coal' && (
                            <label>
                              Opening ash (%)
                              <input
                                type="number"
                                disabled={!canEdit}
                                value={d.opening_ash ?? ''}
                                onChange={(e) =>
                                  edit({
                                    ...inputs,
                                    destinations: inputs.destinations.map((x, j) =>
                                      i === j
                                        ? {
                                            ...x,
                                            opening_ash:
                                              e.target.value === '' ? null : +e.target.value,
                                          }
                                        : x,
                                    ),
                                  })
                                }
                              />
                            </label>
                          )}
                          <div className="stock-value">
                            <b>{stock ? number(stock.closing) : '—'}</b>
                            <span>t closing stock {stale ? '(stale run)' : ''}</span>
                          </div>
                          <progress max={d.capacity} value={stock?.closing || d.opening} />
                          <div className="stock-summary">
                            <span>
                              Receipts <b>{stock ? number(stock.receipts) : '—'} t</b>
                            </span>
                            <span>
                              Reclaim <b>Not modelled</b>
                            </span>
                            {d.material === 'coal' && (
                              <span>
                                Weighted ash{' '}
                                <b>
                                  {stock?.ash != null ? number(stock.ash, 2) + '%' : 'Undefined'}
                                </b>
                              </span>
                            )}
                          </div>
                        </section>
                      );
                    })}
                  </div>
                  {run?.result && (
                    <section className="panel">
                      <div className="panel-title">
                        <h2>Daily production</h2>
                        <span>Receipts on {inputs.timezone} dates</span>
                      </div>
                      <table>
                        <thead>
                          <tr>
                            <th>DATE</th>
                            <th>COAL t</th>
                            <th>WASTE t</th>
                            <th>TOTAL t</th>
                          </tr>
                        </thead>
                        <tbody>
                          {run.result.periods.map((p) => (
                            <tr key={p.date}>
                              <td>{p.date}</td>
                              <td>{number(p.coal, 2)}</td>
                              <td>{number(p.waste, 2)}</td>
                              <td>{number(p.coal + p.waste, 2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </section>
                  )}
                </>
              )}
              {tab === 'scenarios' && (
                <>
                  <div className="section-intro row between">
                    <div>
                      <h2>Plan alternatives</h2>
                      <p>
                        Each branch has independent inputs. Completed run snapshots never change.
                      </p>
                    </div>
                    {canEdit && (
                      <button
                        className="primary"
                        onClick={() => {
                          setBranchName(`${scenario.name} · alternative`);
                          setModal('branch');
                        }}
                      >
                        <GitBranch size={16} />
                        Branch scenario
                      </button>
                    )}
                  </div>
                  <div className="scenario-cards">
                    {scenarios.map((s) => {
                      const latest = runs.find((r) => r.scenario_id === s.id);
                      return (
                        <section
                          className={`panel scenario-card ${s.id === scenario.id ? 'chosen' : ''}`}
                          key={s.id}
                        >
                          <div className="row between">
                            <GitBranch size={22} />
                            {s.id === scenario.id && <span className="badge good">Current</span>}
                          </div>
                          <h2>{s.name}</h2>
                          <p>
                            Revision {s.revision} · {s.inputs.blocks.length} blocks
                          </p>
                          <div className="scenario-facts">
                            <span>
                              Mining rate{' '}
                              <b>
                                {number(
                                  s.inputs.resources.reduce(
                                    (n, r) => n + r.rate * r.utilization,
                                    0,
                                  ),
                                )}{' '}
                                t/h
                              </b>
                            </span>
                            <span>
                              Horizon <b>{s.inputs.calendar.days} days</b>
                            </span>
                            <span>
                              Latest run <b>{latest?.status || 'Not run'}</b>
                            </span>
                          </div>
                          <button className="secondary" onClick={() => onSelectScenario(s.id)}>
                            Open scenario
                            <ArrowUpRight size={16} />
                          </button>
                        </section>
                      );
                    })}
                  </div>
                  <section className="panel">
                    <div className="panel-title">
                      <h2>Run history</h2>
                      <span>Immutable input snapshots and lineage</span>
                    </div>
                    <div className="table-scroll">
                      <table>
                        <thead>
                          <tr>
                            <th>RUN</th>
                            <th>SCENARIO</th>
                            <th>REVISION</th>
                            <th>CREATED (UTC)</th>
                            <th>STATUS</th>
                            <th>REVIEW</th>
                          </tr>
                        </thead>
                        <tbody>
                          {runs.map((r) => (
                            <tr key={r.id}>
                              <td>
                                <code>{r.id.slice(0, 8)}</code>
                              </td>
                              <td>{scenarios.find((s) => s.id === r.scenario_id)?.name}</td>
                              <td>{r.revision}</td>
                              <td>{r.created.slice(0, 19).replace('T', ' ')}</td>
                              <td>
                                <Badge status={r.status} />
                              </td>
                              <td>{r.approved_by || 'Not approved'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {!runs.length && (
                      <div className="empty-small">
                        No runs yet. Open a scenario and run the schedule.
                      </div>
                    )}
                  </section>
                </>
              )}
              {tab === 'reports' && (
                <>
                  <section className="panel report-overview">
                    <FileBarChart size={36} />
                    <div>
                      <h2>
                        {run?.result
                          ? 'Your production plan, with the evidence.'
                          : 'Run a schedule to create reports.'}
                      </h2>
                      <p>
                        Every export includes the selected run and its physical quantities. JSON
                        contains the full immutable input snapshot and result.
                      </p>
                    </div>
                    {run && <Badge status={run.approved_at ? 'approved' : run.status} />}
                  </section>
                  {run?.result && (
                    <>
                      <div className="export-grid">
                        {[
                          {
                            id: 'csv',
                            title: 'Schedule CSV',
                            desc: 'Allocation rows, quantities and input hash.',
                          },
                          {
                            id: 'xlsx',
                            title: 'Excel workbook',
                            desc: 'Allocations, reconciled totals and provenance.',
                          },
                          {
                            id: 'pdf',
                            title: 'Planning summary',
                            desc: 'Physical totals, run assumptions and activities.',
                          },
                          {
                            id: 'json',
                            title: 'Engineering archive',
                            desc: 'Full inputs, results and manifest for review.',
                          },
                        ].map((f) => (
                          <a
                            className="panel export-card"
                            key={f.id}
                            href={`/api/runs/${run.id}/export/${f.id}`}
                            download
                          >
                            <span className="file-type">{f.id.toUpperCase()}</span>
                            <h3>{f.title}</h3>
                            <p>{f.desc}</p>
                            <span className="download-label">
                              Download
                              <Download size={16} />
                            </span>
                          </a>
                        ))}
                      </div>
                      <section className="panel review-panel">
                        <div>
                          <h2>Review & approve</h2>
                          <p>
                            Approval freezes this run as a reviewed revision. It does not certify
                            geotechnical safety or reserves.
                          </p>
                          <dl>
                            <dt>Run</dt>
                            <dd>{run.id}</dd>
                            <dt>Input hash</dt>
                            <dd>
                              <code>{run.input_hash}</code>
                            </dd>
                            <dt>Engine</dt>
                            <dd>{run.result.engine}</dd>
                            <dt>Violations</dt>
                            <dd>{run.result.violations.length}</dd>
                            <dt>Approved by</dt>
                            <dd>{run.approved_by || 'Not approved'}</dd>
                          </dl>
                        </div>
                        {canApprove && (
                          <button
                            className="primary"
                            disabled={busy || run.status !== 'feasible' || !!run.approved_at}
                            onClick={() =>
                              perform(async () => {
                                await post(`/runs/${run.id}/approve`);
                                setRun(await api(`/runs/${run.id}`));
                                setSuccess(
                                  'Run approved. The reviewed input snapshot is preserved.',
                                );
                              })
                            }
                          >
                            <ShieldCheck size={17} />
                            {run.approved_at ? 'Approved' : 'Approve validated run'}
                          </button>
                        )}
                      </section>
                    </>
                  )}
                </>
              )}
              {tab === 'team' && (
                <section className="panel">
                  <div className="panel-title">
                    <h2>Project access</h2>
                    <ShieldCheck size={19} />
                  </div>
                  <table>
                    <thead>
                      <tr>
                        <th>NAME</th>
                        <th>ACCOUNT</th>
                        <th>ROLE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {members.map((m) => (
                        <tr key={m.email}>
                          <td>{m.name}</td>
                          <td>{m.email}</td>
                          <td>
                            <Badge status={m.role} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {project?.role === 'owner' && (
                    <form
                      className="member-form"
                      onSubmit={(e) => {
                        e.preventDefault();
                        perform(async () => {
                          await post(`/projects/${projectId}/members`, {
                            email: memberEmail,
                            role: memberRole,
                          });
                          setSuccess('Project membership updated.');
                          setMemberEmail('');
                        });
                      }}
                    >
                      <label>
                        Existing account email
                        <input
                          required
                          type="email"
                          value={memberEmail}
                          onChange={(e) => setMemberEmail(e.target.value)}
                        />
                      </label>
                      <label>
                        Project role
                        <select value={memberRole} onChange={(e) => setMemberRole(e.target.value)}>
                          <option value="viewer">Viewer</option>
                          <option value="planner">Planner</option>
                          <option value="reviewer">Reviewer</option>
                        </select>
                      </label>
                      <button className="primary" disabled={busy}>
                        <Plus size={16} />
                        Add / update access
                      </button>
                    </form>
                  )}
                  <p className="panel-note">
                    Owners manage access and approve plans; planners edit and run schedules;
                    reviewers approve; viewers read and export. Accounts are provisioned by a server
                    administrator in this pilot.
                  </p>
                </section>
              )}
              {tab === 'audit' && (
                <section className="panel">
                  <div className="panel-title">
                    <h2>Project activity</h2>
                    <span>Latest 150 events</span>
                  </div>
                  <div className="audit-list">
                    {audit.map((a) => (
                      <div key={a.id}>
                        <span className="audit-icon">
                          <History size={16} />
                        </span>
                        <div>
                          <b>{a.action.replaceAll('.', ' · ')}</b>
                          <p>{a.detail}</p>
                          <small>{a.actor}</small>
                        </div>
                        <time>{a.created.slice(0, 19).replace('T', ' ')} UTC</time>
                      </div>
                    ))}
                    {!audit.length && (
                      <div className="empty-small">
                        No recorded changes yet. Imports, edits, runs and exports appear here.
                      </div>
                    )}
                  </div>
                </section>
              )}
            </>
          )}
          <footer className="page-footer">
            <span>MESSI · Independent engineering workspace</span>
            <span>Metric quantities · Explicit assumptions · Traceable revisions</span>
          </footer>
        </main>
      </div>
      {modal === 'project' && (
        <Modal title="Create a planning project" close={() => setModal('')}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              perform(async () => {
                const p = await post('/projects', {
                  name: newName,
                  crs: newCRS,
                  datum: newDatum,
                  timezone: 'Australia/Brisbane',
                  sample: useSample,
                });
                await loadProjects();
                setProjectId(p.id);
                setModal('');
                setSuccess('Project created.');
              });
            }}
          >
            <label>
              Project name
              <input
                required
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. North pit · 2027 plan"
              />
            </label>
            <label>
              Coordinate reference system
              <input required value={newCRS} onChange={(e) => setNewCRS(e.target.value)} />
            </label>
            <label>
              Vertical datum
              <input required value={newDatum} onChange={(e) => setNewDatum(e.target.value)} />
            </label>
            <p className="muted">
              Timezone: Australia/Brisbane. No automatic CRS or datum conversion is performed.
            </p>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={useSample}
                onChange={(e) => setUseSample(e.target.checked)}
              />
              Start with the synthetic 10-block coal example
            </label>
            <button className="primary full" disabled={busy}>
              <Plus size={17} />
              Create project
            </button>
          </form>
        </Modal>
      )}
      {modal === 'branch' && (
        <Modal title="Branch current scenario" close={() => setModal('')}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              perform(async () => {
                const s = dirty ? await save() : scenario!;
                const branch = await post<Scenario>(`/scenarios/${s.id}/branch`, {
                  name: branchName,
                  revision: s.revision,
                });
                setScenarios([...scenarios, branch]);
                chooseScenario(branch);
                setModal('');
                setSuccess('Independent scenario created.');
              });
            }}
          >
            <p className="muted">
              Copy the current inputs to explore a different fleet, calendar or sequence.
            </p>
            <label>
              Scenario name
              <input required value={branchName} onChange={(e) => setBranchName(e.target.value)} />
            </label>
            <button className="primary full" disabled={busy}>
              <GitBranch size={17} />
              Create branch
            </button>
          </form>
        </Modal>
      )}
      {modal === 'import' && (
        <Modal title="Import block model" close={() => setModal('')}>
          <p className="muted">
            UTF-8 CSV (2,000 blocks) or triangulated OBJ (20,000 vertices) · maximum 2 MB.
            Coordinates are minimum corners. Density is always t/m³. Each coal row requires ash and
            an explicit quality/mass basis.
          </p>
          <a
            className="sample-link"
            href="/api-example.csv"
            onClick={(e) => {
              e.preventDefault();
              const header =
                'id,x,y,z,dx,dy,dz,density,material,basis,ash,predecessors,priority,destination\n';
              const body =
                'B-001,642000,7490000,220,10,10,10,2.5,waste,dry,,,1,dump\nB-002,642000,7490000,210,10,10,10,1.4,coal,dry,10,B-001,2,rom\n';
              const u = URL.createObjectURL(new Blob([header + body], { type: 'text/csv' }));
              const a = document.createElement('a');
              a.href = u;
              a.download = 'messi-block-template.csv';
              a.click();
              setTimeout(() => URL.revokeObjectURL(u), 1000);
            }}
          >
            <Download size={15} />
            Download sample CSV
          </a>
          <label>
            Model type
            <select
              aria-label="Model type"
              value={importKind}
              onChange={(e) => {
                setImportKind(e.target.value);
                setPreview(null);
                setCsvText('');
                setFileName('');
              }}
            >
              <option value="blocks">Planning blocks (CSV)</option>
              <option value="surface">Reference surface (triangular OBJ; view only)</option>
            </select>
          </label>
          <label>
            Coordinate units
            <select
              aria-label="Coordinate units"
              value={csvUnits}
              onChange={(e) => {
                setCsvUnits(e.target.value);
                setPreview(null);
              }}
            >
              <option value="m">Metres</option>
              <option value="ft">Feet (density remains t/m³)</option>
            </select>
          </label>
          <label className="upload-zone">
            <Upload size={27} />
            <b>
              {fileName ||
                (importKind === 'blocks' ? 'Choose a block CSV' : 'Choose a triangular OBJ')}
            </b>
            <span>Validated before commit · surface volume is not calculated</span>
            <input
              aria-label="Block CSV file"
              type="file"
              accept={importKind === 'blocks' ? '.csv,text/csv' : '.obj,text/plain'}
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (file) {
                  setCsvText(await file.text());
                  setFileName(file.name);
                  setPreview(null);
                }
              }}
            />
          </label>
          {preview && (
            <div className={`import-preview ${preview.errors.length ? 'bad' : ''}`}>
              <div>
                <b>
                  {preview.surface
                    ? `${preview.surface.faces.length} valid triangles`
                    : `${preview.blocks.length} valid blocks`}
                </b>
                <span>
                  {preview.surface
                    ? `${preview.surface.vertices.length} vertices · view only`
                    : `${number(preview.volume)} m³ · ${number(preview.tonnes)} t`}
                </span>
              </div>
              {preview.errors.length ? (
                <>
                  <strong>{preview.errors.length} errors — nothing committed</strong>
                  <ul>
                    {preview.errors.map((e: any, i: number) => (
                      <li key={i}>
                        Row {e.row}: {e.message}
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <p>
                  <CheckCircle2 size={16} />
                  {preview.surface
                    ? 'Surface topology checked; no solid-volume claim.'
                    : 'Units, IDs, geometry, dependencies and destinations validated.'}
                </p>
              )}
            </div>
          )}
          <div className="modal-actions">
            <button
              className="secondary"
              disabled={!csvText || busy}
              onClick={() =>
                perform(async () => {
                  if (dirty) throw new Error('Save or discard current changes before importing.');
                  if (importKind === 'surface') {
                    setPreview(
                      await post(`/scenarios/${scenario!.id}/surface-preview`, {
                        revision: scenario!.revision,
                        content: csvText,
                        name: fileName,
                        units: csvUnits,
                      }),
                    );
                  } else {
                    const form = new FormData();
                    form.append('file', new File([csvText], fileName, { type: 'text/csv' }));
                    setPreview(
                      await api(`/scenarios/${scenario!.id}/import-preview?units=${csvUnits}`, {
                        method: 'POST',
                        body: form,
                      }),
                    );
                  }
                })
              }
            >
              Validate import
            </button>
            <button
              className="primary"
              disabled={!preview || preview.errors.length > 0 || busy}
              onClick={() =>
                perform(async () => {
                  const s = await post<Scenario>(
                    `/scenarios/${scenario!.id}/${importKind === 'surface' ? 'surface' : 'import'}`,
                    {
                      revision: scenario!.revision,
                      content: csvText,
                      units: csvUnits,
                      ...(importKind === 'surface' ? { name: fileName } : {}),
                    },
                  );
                  chooseScenario(s);
                  setScenarios((list) => list.map((x) => (x.id === s.id ? s : x)));
                  setModal('');
                  setSuccess(
                    importKind === 'surface'
                      ? 'Reference surface imported. Original OBJ and hash preserved.'
                      : `${preview.blocks.length} blocks imported. Source hash and original CSV preserved.`,
                  );
                })
              }
            >
              <Check size={17} />
              Commit import
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
function Metric({
  label,
  value,
  unit,
  sub,
  icon,
  accent = 'orange',
}: {
  label: string;
  value: string;
  unit: string;
  sub: string;
  icon: ReactNode;
  accent?: string;
}) {
  return (
    <section className={`metric ${accent}`}>
      <div>
        <span>{label}</span>
        <i>{icon}</i>
      </div>
      <p>
        {value}
        <small>{unit}</small>
      </p>
      <footer>{sub}</footer>
    </section>
  );
}
function Gantt({
  run,
  inputs,
  selected,
  select,
}: {
  run: Run;
  inputs: Inputs;
  selected: string | null;
  select: (id: string) => void;
}) {
  const allocations = run.result!.allocations;
  const first = Math.min(...allocations.map((a) => +new Date(a.start)));
  const last = Math.max(...allocations.map((a) => +new Date(a.end)));
  const days = Number.isFinite(first) ? Math.max(5, Math.ceil((last - first) / 86400000) + 1) : 5;
  const span = days * 86400000;
  const format = (dt: number) =>
    new Intl.DateTimeFormat('en-AU', {
      day: '2-digit',
      month: 'short',
      timeZone: inputs.timezone,
    }).format(dt);
  return (
    <div className="gantt-scroll">
      <div className="gantt" style={{ minWidth: Math.max(650, days * 65 + 180) }}>
        <div className="gantt-heading">
          <span>ACTIVITY / MATERIAL</span>
          <div>
            {Array.from({ length: days }, (_, i) => (
              <span key={i}>{Number.isFinite(first) ? format(first + i * 86400000) : '—'}</span>
            ))}
          </div>
        </div>
        {inputs.blocks.map((b) => (
          <div className={`gantt-row ${selected === b.id ? 'selected' : ''}`} key={b.id}>
            <button onClick={() => select(b.id)}>
              <i className={`swatch ${b.material}`} />
              {b.id}
              {b.locked_start && <LockKeyhole size={11} />}
            </button>
            <div className="gantt-track" style={{ backgroundSize: `${100 / days}% 100%` }}>
              {allocations
                .filter((a) => a.block_id === b.id)
                .map((a, i) => (
                  <button
                    aria-label={`Schedule ${b.id} segment ${i + 1}`}
                    key={i}
                    title={`${b.id} · ${number(a.tonnes)} t · ${a.resource_id}\n${a.start} – ${a.end}`}
                    className={`gantt-bar ${b.material}`}
                    style={{
                      left: `${((+new Date(a.start) - first) / span) * 100}%`,
                      width: `${Math.max(0.2, ((+new Date(a.end) - +new Date(a.start)) / span) * 100)}%`,
                    }}
                    onClick={() => select(b.id)}
                  />
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
