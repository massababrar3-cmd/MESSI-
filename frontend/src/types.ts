export type User = { id: string; name: string; email: string };
export type Project = {
  id: string;
  name: string;
  crs: string;
  datum: string;
  timezone: string;
  role: string;
  created: string;
};
export type Block = {
  id: string;
  x: number;
  y: number;
  z: number;
  dx: number;
  dy: number;
  dz: number;
  density: number;
  material: 'coal' | 'waste';
  basis: 'dry' | 'as_received';
  ash: number | null;
  predecessors: string[];
  priority: number;
  destination: string;
  locked_start: string | null;
  locked_resource: string | null;
};
export type Resource = {
  id: string;
  name: string;
  rate: number;
  utilization: number;
  materials: ('coal' | 'waste')[];
  outages: string[];
};
export type Destination = {
  id: string;
  name: string;
  material: 'coal' | 'waste';
  basis: string;
  capacity: number;
  opening: number;
  opening_ash: number | null;
};
export type Surface = {
  id: string;
  name: string;
  vertices: [number, number, number][];
  faces: [number, number, number][];
  closed: boolean;
  source_hash: string;
  original_obj: string;
};
export type Inputs = {
  blocks: Block[];
  surfaces?: Surface[];
  resources: Resource[];
  destinations: Destination[];
  calendar: {
    start: string;
    days: number;
    shift_start: number;
    shift_hours: number;
    weekdays: number[];
  };
  timezone: string;
  source: Record<string, unknown>;
};
export type Scenario = {
  id: string;
  project_id: string;
  name: string;
  revision: number;
  parent_id: string | null;
  inputs: Inputs;
};
export type Allocation = {
  block_id: string;
  resource_id: string;
  destination: string;
  start: string;
  end: string;
  tonnes: number;
  hours: number;
  material: string;
  basis: string;
  ash: number | null;
};
export type Result = {
  status: string;
  engine: string;
  allocations: Allocation[];
  activities: {
    id: string;
    start: string | null;
    end: string | null;
    tonnes: number;
    hours: number;
    complete: boolean;
  }[];
  unscheduled: { id: string; reason: string }[];
  violations: string[];
  totals: { tonnes: number; coal: number; waste: number; volume: number };
  periods: { date: string; coal: number; waste: number }[];
  stocks: {
    id: string;
    name: string;
    material: string;
    basis: string;
    opening: number;
    receipts: number;
    reclaim: number;
    loss: number;
    closing: number;
    capacity: number;
    ash: number | null;
  }[];
};
export type Run = {
  id: string;
  project_id: string;
  scenario_id: string;
  revision: number;
  created: string;
  input_hash: string;
  status: string;
  progress: number;
  error: string | null;
  approved_by: string | null;
  approved_at: string | null;
  result?: Result | null;
  snapshot?: Inputs;
};
