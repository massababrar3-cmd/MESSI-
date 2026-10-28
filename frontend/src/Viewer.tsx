import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Expand, Layers3, Compass, ScanLine, Ruler, RotateCcw } from 'lucide-react';
import type { Block, Run, Surface } from './types';
import { number } from './api';

type Props = {
  blocks: Block[];
  surfaces: Surface[];
  selected: string | null;
  onSelect: (id: string) => void;
  run: Run | null;
  date: string;
};
export default function Viewer({ blocks, surfaces, selected, onSelect, run, date }: Props) {
  const savedView = useRef<{ key: string; position: THREE.Vector3; target: THREE.Vector3 } | null>(
    null,
  );
  const host = useRef<HTMLDivElement>(null);
  const selectRef = useRef(onSelect);
  selectRef.current = onSelect;
  const [showSurface, setShowSurface] = useState(true);
  const [coal, setCoal] = useState(true),
    [waste, setWaste] = useState(true),
    [section, setSection] = useState(false),
    [level, setLevel] = useState(100),
    [top, setTop] = useState(false),
    [error, setError] = useState(''),
    [reset, setReset] = useState(0),
    [measure, setMeasure] = useState(false),
    [points, setPoints] = useState<Block[]>([]);
  const measureRef = useRef(measure);
  measureRef.current = measure;
  useEffect(() => {
    if (!host.current) return;
    const element = host.current;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
      setError('');
    } catch {
      setError(
        '3D rendering requires WebGL2. Enable hardware acceleration or use a supported Chrome/Edge browser.',
      );
      return;
    }
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.setClearColor('#111c2b');
    renderer.localClippingEnabled = true;
    renderer.domElement.setAttribute('aria-label', 'Interactive 3D mine model');
    renderer.domElement.setAttribute('data-testid', 'mine-canvas');
    element.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog('#111c2b', 1000, 4000);
    const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 10000);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    const bounds = new THREE.Box3();
    for (const b of blocks) {
      bounds.expandByPoint(new THREE.Vector3(b.x, b.y, b.z));
      bounds.expandByPoint(new THREE.Vector3(b.x + b.dx, b.y + b.dy, b.z + b.dz));
    }
    for (const s of surfaces)
      for (const v of s.vertices) bounds.expandByPoint(new THREE.Vector3(...v));
    if (bounds.isEmpty()) {
      bounds.min.set(0, 0, 0);
      bounds.max.set(200, 100, 50);
    }
    const center = bounds.getCenter(new THREE.Vector3());
    const size = bounds.getSize(new THREE.Vector3());
    const extent = Math.max(size.x, size.y, size.z, 100);
    camera.position.set(
      top ? 0 : extent * 0.9,
      top ? extent * 1.7 : extent * 0.95,
      top ? 0.01 : extent * 1.3,
    );
    controls.target.set(0, size.z / 2, 0);
    camera.lookAt(controls.target);
    const viewKey = [
      bounds.min.toArray().join(','),
      bounds.max.toArray().join(','),
      top,
      reset,
    ].join(':');
    if (savedView.current?.key === viewKey) {
      camera.position.copy(savedView.current.position);
      controls.target.copy(savedView.current.target);
    }
    const ambient = new THREE.HemisphereLight(0xc9dff5, 0x554738, 2.8);
    scene.add(ambient);
    const sunlight = new THREE.DirectionalLight(0xffffff, 3.5);
    sunlight.position.set(100, 300, 200);
    scene.add(sunlight);
    const grid = new THREE.GridHelper(Math.ceil((extent * 2) / 100) * 100, 24, 0x536174, 0x263548);
    grid.position.y = -0.3;
    scene.add(grid);
    const geom = new THREE.BoxGeometry(1, 1, 1),
      material = new THREE.MeshStandardMaterial({ roughness: 0.8, metalness: 0.05 });
    if (section)
      material.clippingPlanes = [
        new THREE.Plane(new THREE.Vector3(0, -1, 0), (size.z * level) / 100),
      ];
    const mesh = new THREE.InstancedMesh(geom, material, blocks.length);
    mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    const transform = new THREE.Object3D();
    const color = new THREE.Color();
    const edges: THREE.LineSegments[] = [];
    const completed = new Set(
      run?.result?.activities
        .filter(
          (a) =>
            a.end &&
            date &&
            new Intl.DateTimeFormat('en-CA', {
              timeZone: run?.snapshot?.timezone || 'Australia/Brisbane',
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
            }).format(new Date(a.end)) <= date,
        )
        .map((a) => a.id) || [],
    );
    const hidden = new Set<number>();
    blocks.forEach((b, i) => {
      const visible = b.material === 'coal' ? coal : waste;
      if (!visible) hidden.add(i);
      transform.position.set(
        b.x + b.dx / 2 - center.x,
        b.z + b.dz / 2 - bounds.min.z,
        -(b.y + b.dy / 2 - center.y),
      );
      transform.scale.set(
        visible ? b.dx * 0.985 : 0,
        visible ? b.dz * 0.985 : 0,
        visible ? b.dy * 0.985 : 0,
      );
      transform.updateMatrix();
      mesh.setMatrixAt(i, transform.matrix);
      color.set(
        b.id === selected
          ? '#ffb24b'
          : completed.has(b.id)
            ? '#344457'
            : b.material === 'coal'
              ? '#3ab2a3'
              : '#ba8f5b',
      );
      mesh.setColorAt(i, color);
      if (visible) {
        const edge = new THREE.LineSegments(
          new THREE.EdgesGeometry(geom),
          new THREE.LineBasicMaterial({
            color: b.id === selected ? 0xffdf9d : 0x15202d,
            transparent: true,
            opacity: 0.8,
          }),
        );
        edge.position.copy(transform.position);
        edge.scale.copy(transform.scale);
        scene.add(edge);
        edges.push(edge);
      }
    });
    mesh.computeBoundingSphere();
    scene.add(mesh);
    const surfaceMeshes: THREE.Mesh[] = [];
    if (showSurface)
      for (const s of surfaces) {
        const geometry = new THREE.BufferGeometry();
        const vertices = s.vertices.flatMap((v) => [
          v[0] - center.x,
          v[2] - bounds.min.z,
          -(v[1] - center.y),
        ]);
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.setIndex(s.faces.flat());
        geometry.computeVertexNormals();
        const mat = new THREE.MeshStandardMaterial({
          color: '#6e8e9c',
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.45,
          roughness: 1,
          wireframe: false,
        });
        if (section)
          mat.clippingPlanes = [
            new THREE.Plane(new THREE.Vector3(0, -1, 0), (size.z * level) / 100),
          ];
        const item = new THREE.Mesh(geometry, mat);
        scene.add(item);
        surfaceMeshes.push(item);
      }
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let down = [0, 0];
    const onDown = (event: PointerEvent) => {
      down = [event.clientX, event.clientY];
    };
    const onClick = (event: PointerEvent) => {
      if (Math.hypot(event.clientX - down[0], event.clientY - down[1]) > 5) return;
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.set(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        (-(event.clientY - rect.top) / rect.height) * 2 + 1,
      );
      raycaster.setFromCamera(mouse, camera);
      const hit = raycaster
        .intersectObject(mesh)
        .find((h) => h.instanceId !== undefined && !hidden.has(h.instanceId));
      if (hit?.instanceId !== undefined) {
        const b = blocks[hit.instanceId];
        selectRef.current(b.id);
        if (measureRef.current) setPoints((p) => (p.length === 1 ? [p[0], b] : [b]));
      }
    };
    renderer.domElement.addEventListener('pointerdown', onDown);
    renderer.domElement.addEventListener('pointerup', onClick);
    const resize = new ResizeObserver(() => {
      const w = element.clientWidth,
        h = element.clientHeight;
      renderer.setSize(w, h);
      camera.aspect = w / Math.max(h, 1);
      camera.updateProjectionMatrix();
    });
    resize.observe(element);
    let frame = 0;
    const draw = () => {
      frame = requestAnimationFrame(draw);
      controls.update();
      renderer.render(scene, camera);
    };
    draw();
    return () => {
      savedView.current = {
        key: viewKey,
        position: camera.position.clone(),
        target: controls.target.clone(),
      };
      cancelAnimationFrame(frame);
      resize.disconnect();
      controls.dispose();
      for (const s of surfaceMeshes) {
        s.geometry.dispose();
        (s.material as THREE.Material).dispose();
      }
      geom.dispose();
      material.dispose();
      for (const e of edges) {
        e.geometry.dispose();
        (e.material as THREE.Material).dispose();
      }
      grid.geometry.dispose();
      (grid.material as THREE.Material).dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, [
    blocks,
    surfaces,
    showSurface,
    selected,
    coal,
    waste,
    section,
    level,
    top,
    reset,
    run?.id,
    run?.status,
    date,
  ]);
  const distance =
    points.length === 2
      ? Math.hypot(points[1].x - points[0].x, points[1].y - points[0].y, points[1].z - points[0].z)
      : null;
  return (
    <div className="viewer-shell">
      <div className="viewer-tools">
        <span>
          <Layers3 size={15} />
          MODEL VIEW
        </span>
        <div className="segmented">
          <button className={!top ? 'active' : ''} onClick={() => setTop(false)}>
            Perspective
          </button>
          <button className={top ? 'active' : ''} onClick={() => setTop(true)}>
            Plan
          </button>
        </div>
        <button
          title="Reset view"
          aria-label="Reset 3D view"
          onClick={() => setReset((x) => x + 1)}
        >
          <RotateCcw size={16} />
        </button>
        <button
          title="Cross section"
          aria-label="Cross section"
          className={section ? 'active' : ''}
          onClick={() => setSection(!section)}
        >
          <ScanLine size={17} />
        </button>
        <button
          title="Measure between block origins"
          aria-label="Measure block origins"
          className={measure ? 'active' : ''}
          onClick={() => {
            setMeasure(!measure);
            setPoints([]);
          }}
        >
          <Ruler size={17} />
        </button>
        <button
          title="Expand model view"
          aria-label="Expand model view"
          onClick={() => host.current?.parentElement?.requestFullscreen()}
        >
          <Expand size={16} />
        </button>
      </div>
      <div className="viewer-canvas" ref={host} />
      {error && <div className="viewer-error">{error}</div>}
      {!blocks.length && <div className="viewer-empty">Import a block model to start planning</div>}
      <div className="north">
        <Compass size={30} />
        <b>N</b>
      </div>
      <div className="model-tag">
        <span className="live-dot" />
        LOCAL RENDER ORIGIN · METRES
      </div>
      <div className="viewer-legend">
        <label>
          <input type="checkbox" checked={waste} onChange={(e) => setWaste(e.target.checked)} />
          <i className="swatch waste" />
          Waste
        </label>
        <label>
          <input type="checkbox" checked={coal} onChange={(e) => setCoal(e.target.checked)} />
          <i className="swatch coal" />
          Coal
        </label>
        <label>
          <input
            type="checkbox"
            checked={showSurface}
            onChange={(e) => setShowSurface(e.target.checked)}
          />
          Surfaces ({surfaces.length})
        </label>
        <span>Drag to orbit · scroll to zoom · click to inspect</span>
      </div>
      {section && (
        <div className="section-control">
          <label>
            Section elevation {level}%
            <input
              aria-label="Section elevation"
              type="range"
              min="0"
              max="100"
              value={level}
              onChange={(e) => setLevel(+e.target.value)}
            />
          </label>
        </div>
      )}
      {measure && (
        <div className="measure-hint">
          {distance === null
            ? 'Select two block origins to measure distance'
            : `${points[0].id} → ${points[1].id}: ${number(distance, 3)} m (origin to origin)`}
        </div>
      )}
    </div>
  );
}
