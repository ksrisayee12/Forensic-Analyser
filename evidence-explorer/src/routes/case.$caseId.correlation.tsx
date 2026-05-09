import { createFileRoute, useParams } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import * as d3 from "d3";
import { getCorrelationGraph } from "@/services/api";
import type { GraphNode, GraphEdge } from "@/types";
import { X, ZoomIn, ZoomOut, Maximize2, User, MapPin, Smartphone, Zap, ChevronRight, Filter, Layers, Target, Clock } from "lucide-react";

interface PositionedNode extends GraphNode { x: number; y: number; vx?: number; vy?: number; fx?: number | null; fy?: number | null; isCluster?: boolean; childCount?: number; }
interface PositionedEdge extends Omit<GraphEdge, "source" | "target"> { source: any; target: any; }

const typeColor: Record<GraphNode["type"], string> = { person: "#C38EB4", location: "#86A8CF", device: "#c8bfaf", event: "#26425A" };
const typeIcon = { person: User, location: MapPin, device: Smartphone, event: Zap };

export const Route = createFileRoute("/case/$caseId/correlation")({
  component: CorrelationPage,
});

function CorrelationPage() {
  const { caseId } = useParams({ from: "/case/$caseId/correlation" });
  
  // Data State
  const [allNodes, setAllNodes] = useState<PositionedNode[]>([]);
  const [allEdges, setAllEdges] = useState<PositionedEdge[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Interaction State
  const [hover, setHover] = useState<PositionedNode | null>(null);
  const [selected, setSelected] = useState<PositionedNode | null>(null);
  const [breadcrumbs, setBreadcrumbs] = useState<PositionedNode[]>([]);
  
  // Filter/Tool State
  const [minConfidence, setMinConfidence] = useState(0);
  const [timeRange, setTimeRange] = useState<[number, number] | null>(null);
  const [globalTimeBounds, setGlobalTimeBounds] = useState<[number, number] | null>(null);
  const [clustering, setClustering] = useState(false);
  const [focusMode, setFocusMode] = useState(false);

  // SVG State
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const transformRef = useRef(transform);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);

  const [clusterPositions, setClusterPositions] = useState<Record<string, {x: number, y: number}>>({});

  useEffect(() => {
    transformRef.current = transform;
  }, [transform]);

  // 1. Load Data
  useEffect(() => {
    getCorrelationGraph(caseId).then(({ nodes: ns, edges: es }) => {
      // Concentric rings initial positions centered at 400,300
      const parsedNodes = ns.map((n, i) => {
        const ringIndex = i % 3;
        const radius = 140 + ringIndex * 110;
        const perRing = Math.ceil(ns.length / 3);
        const angle = ((Math.floor(i / 3)) / perRing) * Math.PI * 2 + ringIndex * 0.4;
        return { ...n, x: 400 + Math.cos(angle) * radius, y: 300 + Math.sin(angle) * radius };
      });
      
      let minT = Infinity; let maxT = -Infinity;
      parsedNodes.forEach(n => {
        if (n.evidenceData?.timestamp) {
          const t = new Date(n.evidenceData.timestamp).getTime();
          if (!isNaN(t)) { minT = Math.min(minT, t); maxT = Math.max(maxT, t); }
        }
      });
      if (minT !== Infinity) {
        setGlobalTimeBounds([minT, maxT]);
        setTimeRange([minT, maxT]);
      }
      
      setAllNodes(parsedNodes);
      setAllEdges(es.map(e => ({ ...e, source: e.source, target: e.target })));
      setLoading(false);
    });
  }, [caseId]);

  // 2. Derive Visible Graph (Filtering & Clustering)
  const { visibleNodes, visibleEdges } = useMemo(() => {
    if (allNodes.length === 0) return { visibleNodes: [], visibleEdges: [] };

    let nodes = [...allNodes];
    let edges = allEdges.filter(e => (e.confidence ?? 100) >= minConfidence);

    // Temporal Filter
    if (timeRange && globalTimeBounds) {
      nodes = nodes.filter(n => {
        if (!n.evidenceData?.timestamp) return true; // keep context nodes without time
        const t = new Date(n.evidenceData.timestamp).getTime();
        return isNaN(t) || t <= timeRange[1]; // Filter out events happening AFTER the slider
      });
    }

    // Entity Clustering (Macro Nodes by Type)
    if (clustering) {
      const clusteredNodes: PositionedNode[] = [];
      const typeGroups = d3.group(nodes, d => d.type);
      typeGroups.forEach((group, type) => {
        const clusterId = `cluster-${type}`;
        const defaultX = d3.mean(group, d => d.x) || 0;
        const defaultY = d3.mean(group, d => d.y) || 0;
        
        clusteredNodes.push({
          id: clusterId,
          label: `${type.toUpperCase()} CLUSTER`,
          type: type as any,
          x: clusterPositions[clusterId]?.x ?? defaultX,
          y: clusterPositions[clusterId]?.y ?? defaultY,
          isCluster: true,
          childCount: group.length,
        });
      });
      nodes = clusteredNodes;
      
      const newEdges: PositionedEdge[] = [];
      const edgeMap = new Map();
      edges.forEach(e => {
         const sId = typeof e.source === 'string' ? e.source : e.source.id;
         const tId = typeof e.target === 'string' ? e.target : e.target.id;
         const sType = allNodes.find(n => n.id === sId)?.type;
         const tType = allNodes.find(n => n.id === tId)?.type;
         if (sType && tType && sType !== tType) {
           const key = `${sType}-${tType}`;
           if (!edgeMap.has(key)) {
             edgeMap.set(key, true);
             newEdges.push({ ...e, source: `cluster-${sType}`, target: `cluster-${tType}` } as any);
           }
         }
      });
      edges = newEdges;
    }

    // Ensure edges only connect visible nodes
    const nodeIds = new Set(nodes.map(n => n.id));
    edges = edges.filter(e => {
       const s = typeof e.source === 'string' ? e.source : e.source.id;
       const t = typeof e.target === 'string' ? e.target : e.target.id;
       return nodeIds.has(s) && nodeIds.has(t);
    });

    return { visibleNodes: nodes, visibleEdges: edges };
  }, [allNodes, allEdges, minConfidence, timeRange, clustering]);

  const nodeMap = useMemo(() => Object.fromEntries(visibleNodes.map(n => [n.id, n])), [visibleNodes]);
  const focusMap = useMemo(() => {
    if (!focusMode || !selected) return null;
    const map = new Set([selected.id]);
    visibleEdges.forEach(e => {
      const s = typeof e.source === 'string' ? e.source : e.source.id;
      const t = typeof e.target === 'string' ? e.target : e.target.id;
      if (s === selected.id) map.add(t);
      if (t === selected.id) map.add(s);
    });
    return map;
  }, [focusMode, selected, visibleEdges]);

  // 3. Selection & Breadcrumbs
  const handleSelect = useCallback((n: PositionedNode) => {
    setSelected(n);
    if (!breadcrumbs.find(b => b.id === n.id)) {
      setBreadcrumbs(prev => [...prev, n]);
    }
    // Center Graph smoothly
    if (svgRef.current && zoomRef.current) {
      const svg = svgRef.current;
      d3.select(svg).transition().duration(750).call(
        zoomRef.current.transform, 
        d3.zoomIdentity.translate(svg.clientWidth/2 - n.x, svg.clientHeight/2 - n.y)
      );
    }
  }, [breadcrumbs]);

  const jumpBreadcrumb = (index: number, n: PositionedNode) => {
    setBreadcrumbs(prev => prev.slice(0, index + 1));
    handleSelect(n);
  };

  // 4. Manual Drag Setup (No Physics)
  useEffect(() => {
    if (!svgRef.current || visibleNodes.length === 0) return;
    
    const drag = d3.drag<SVGGElement, unknown>()
      .on("start", function() {
        d3.select(this).raise();
      })
      .on("drag", function(event) {
        const id = this.getAttribute("data-id");
        if (!id) return;
        const k = transformRef.current.k;
        
        if (id.startsWith('cluster-')) {
          setClusterPositions(prev => ({
             ...prev, 
             [id]: { x: (prev[id]?.x || visibleNodes.find(n => n.id === id)!.x) + event.dx/k, 
                     y: (prev[id]?.y || visibleNodes.find(n => n.id === id)!.y) + event.dy/k }
          }));
        } else {
          setAllNodes(prev => prev.map(n => 
            n.id === id ? { ...n, x: n.x + event.dx / k, y: n.y + event.dy / k } : n
          ));
        }
      });

    d3.select(svgRef.current).selectAll<SVGGElement, unknown>(".graph-node").call(drag as any);

    return () => {
      d3.select(svgRef.current).selectAll(".graph-node").on(".drag", null);
    };
  }, [visibleNodes.length]); // Re-attach if node count changes

  // 5. SVG Drag & Zoom Setup
  useEffect(() => {
    if (!svgRef.current || loading) return;
    const svg = d3.select(svgRef.current);

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .filter((event) => {
        if (event.type === "wheel") {
          return event.ctrlKey || event.metaKey;
        }
        return !event.ctrlKey && !event.button;
      })
      .on("zoom", (event) => setTransform({ x: event.transform.x, y: event.transform.y, k: event.transform.k }));
    
    zoomRef.current = zoom;
    svg.call(zoom);

    svg.on("dblclick.zoom", function (event) {
      event.preventDefault();
      const [mx, my] = d3.pointer(event);
      const t = d3.zoomTransform(this);
      const newK = Math.min(4, t.k * 1.5);
      const nx = mx - (mx - t.x) * (newK / t.k);
      const ny = my - (my - t.y) * (newK / t.k);
      d3.select(this).transition().duration(450).call(zoom.transform, d3.zoomIdentity.translate(nx, ny).scale(newK));
    });

    return () => { svg.on(".zoom", null); };
  }, [loading]);

  // End of setup



  if (loading) return <div className="p-8 text-sm text-muted-foreground">Building correlation graph…</div>;
  if (allNodes.length === 0) return <div className="p-8 text-sm text-muted-foreground">No correlation data for this case.</div>;

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] w-full overflow-hidden bg-background">
      {/* Breadcrumbs Top Bar */}
      <div className="flex items-center h-10 px-4 border-b border-white/5 shrink-0 overflow-x-auto" style={{ background: "#08080a" }}>
        <div className="flex items-center text-[12px]">
          <span className="text-muted-foreground/30 font-medium mr-2 data-mono text-[10px] tracking-widest uppercase">Path:</span>
          {breadcrumbs.length === 0 ? <span className="text-muted-foreground/25 italic text-[12px]">No node selected</span> : null}
          {breadcrumbs.map((b, i) => (
            <div key={b.id + i} className="flex items-center">
              {i > 0 && <ChevronRight className="h-3 w-3 mx-1 text-muted-foreground/25" />}
              <button 
                onClick={() => jumpBreadcrumb(i, b)}
                className={`px-2 py-1 rounded-md transition-colors text-[12px] ${
                  selected?.id === b.id 
                    ? 'text-primary/80 font-medium' 
                    : 'text-foreground/40 hover:text-foreground/70'
                }`}
              >
                {b.label}
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Side Panel: Evidence Central */}
        <aside
          className="w-64 border-r border-white/5 flex flex-col shrink-0 backdrop-blur-xl"
          style={{ background: "linear-gradient(180deg, #0a0a0d 0%, #0c0c10 100%)" }}
        >
          <div className="p-4 border-b border-white/5">
            <h3 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-foreground/50">Evidence Central</h3>
            <p className="text-[10px] text-muted-foreground/30 mt-0.5">Hierarchical Tree &amp; Filters</p>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            
            {/* Tree View */}
            <div>
              <p className="text-[9px] font-semibold uppercase tracking-[0.2em] text-muted-foreground/30 mb-3">Entities</p>
              <div className="space-y-4">
                {(["person", "location", "device", "event"] as const).map(type => {
                  const typeNodes = allNodes.filter(n => n.type === type);
                  if (typeNodes.length === 0) return null;
                  const Icon = typeIcon[type];
                  return (
                    <div key={type}>
                      <div className="flex items-center gap-2 mb-2" style={{ color: typeColor[type] }}>
                        <Icon className="h-3.5 w-3.5" />
                        <span className="text-[12px] font-medium capitalize opacity-80">{type}s ({typeNodes.length})</span>
                      </div>
                      <ul className="pl-3 space-y-0.5 border-l border-white/5 ml-2">
                        {typeNodes.map(n => (
                          <li key={n.id}>
                            <button 
                              onClick={() => handleSelect(n)}
                              className={`w-full text-left text-[11px] px-2 py-1 rounded truncate transition-colors ${
                                selected?.id === n.id 
                                  ? 'text-foreground/90 font-medium' 
                                  : 'text-muted-foreground/40 hover:text-foreground/60'
                              }`}
                            >
                              {n.label}
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>
            </div>

            <hr className="border-white/5" />

            {/* Filters */}
            <div className="space-y-4">
              <p className="text-[9px] font-semibold uppercase tracking-[0.2em] text-muted-foreground/30">Forensic Controls</p>
              
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-muted-foreground/40">Confidence Threshold</span>
                  <span className="text-primary/70 font-medium data-mono">{minConfidence}%</span>
                </div>
                <input 
                  type="range" min="0" max="100" value={minConfidence} 
                  onChange={e => setMinConfidence(Number(e.target.value))}
                  className="w-full accent-primary"
                />
              </div>

              <label className="flex items-center justify-between text-[12px] cursor-pointer p-2.5 rounded-lg hover:bg-white/[0.03] transition-colors border border-white/5">
                <div className="flex items-center gap-2">
                  <Layers className="h-3.5 w-3.5 text-muted-foreground/40" />
                  <span className="text-foreground/50">Macro Clustering</span>
                </div>
                <input type="checkbox" checked={clustering} onChange={e => setClustering(e.target.checked)} className="accent-primary" />
              </label>

              <label className="flex items-center justify-between text-[12px] cursor-pointer p-2.5 rounded-lg hover:bg-white/[0.03] transition-colors border border-white/5">
                <div className="flex items-center gap-2">
                  <Target className="h-3.5 w-3.5 text-muted-foreground/40" />
                  <span className="text-foreground/50">Focus Mode</span>
                </div>
                <input type="checkbox" checked={focusMode} onChange={e => setFocusMode(e.target.checked)} className="accent-primary" />
              </label>
            </div>
            
          </div>
        </aside>

        {/* Center Graph Area */}
        <div className="flex-1 relative bg-background">
          <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10 rounded-lg border border-white/5 px-3 py-1.5 text-[10px] text-muted-foreground/30 shadow-sm text-center" style={{ background: "rgba(10,10,14,0.8)", backdropFilter: "blur(12px)" }}>
            Ctrl + Scroll to zoom &nbsp;·&nbsp; Drag canvas to pan &nbsp;·&nbsp; Drag nodes to reposition
          </div>

          <svg ref={svgRef} className="w-full h-full cursor-grab active:cursor-grabbing">
            {/* Arrow defs live in JSX so they survive React re-renders */}
            <defs>
              <marker id="arrow" viewBox="0 -5 10 10" refX="22" refY="0" markerWidth="8" markerHeight="8" orient="auto">
                <path d="M0,-5L10,0L0,5" fill="#ffffff" />
              </marker>
              <marker id="arrow-selected" viewBox="0 -5 10 10" refX="22" refY="0" markerWidth="8" markerHeight="8" orient="auto">
                <path d="M0,-5L10,0L0,5" fill="#C38EB4" />
              </marker>
            </defs>
            <g transform={`translate(${transform.x},${transform.y}) scale(${transform.k})`}>
              {/* Edges */}
              <g>
                {visibleEdges.map((e, i) => {
                  // edges store string IDs — look up actual node positions
                  const srcId = typeof e.source === 'string' ? e.source : e.source?.id;
                  const tgtId = typeof e.target === 'string' ? e.target : e.target?.id;
                  const s = nodeMap[srcId];
                  const t = nodeMap[tgtId];
                  if (!s || !t || typeof s.x !== 'number' || typeof t.x !== 'number') return null;
                  
                  const isSrcSelected = s.id === selected?.id || t.id === selected?.id;
                  const isDimmed = focusMap && !focusMap.has(s.id) && !focusMap.has(t.id);
                  const edgeOpacity = isDimmed ? 0.04 : (isSrcSelected ? 1 : 0.75);
                  const edgeColor = isSrcSelected ? "#C38EB4" : "#ffffff";

                  return (
                    <g key={i} opacity={edgeOpacity}>
                      <line 
                        x1={s.x} y1={s.y} x2={t.x} y2={t.y} 
                        stroke={edgeColor}
                        strokeWidth={isSrcSelected ? 2 : 1.2}
                        markerEnd={isSrcSelected ? "url(#arrow-selected)" : "url(#arrow)"} 
                      />
                      {e.label && (
                        <text x={(s.x + t.x) / 2} y={(s.y + t.y) / 2 - 7} fontSize={10} fill="rgba(255,255,255,0.55)" textAnchor="middle" fontFamily="monospace">
                          {e.label}
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
              
              {/* Nodes */}
              <g>
                {visibleNodes.map((n) => {
                  const isHover = hover?.id === n.id;
                  const isSelected = selected?.id === n.id;
                  const isDimmed = focusMap && !focusMap.has(n.id);
                  
                  return (
                    <g 
                      key={n.id}
                      data-id={n.id}
                      transform={`translate(${n.x || 0},${n.y || 0})`}
                      className="graph-node cursor-pointer active:cursor-grabbing"
                      opacity={isDimmed ? 0.1 : 1}
                      onMouseEnter={() => setHover(n)}
                      onMouseLeave={() => setHover(null)}
                      onClick={(e) => { e.stopPropagation(); handleSelect(n); }}
                    >
                      <circle 
                        r={n.isCluster ? 30 : (isHover || isSelected ? 24 : 20)} 
                        fill={typeColor[n.type]} 
                        fillOpacity={isSelected ? 0.35 : (isHover ? 0.25 : 0.15)}
                        stroke={typeColor[n.type]} 
                        strokeWidth={isSelected ? 2 : 1.5}
                        strokeOpacity={isSelected ? 1 : (isHover ? 0.9 : 0.7)}
                        style={{ transition: "r 0.15s ease, stroke-opacity 0.15s ease, fill-opacity 0.15s ease" }}
                      />
                      <circle r={n.isCluster ? 7 : 5} fill={typeColor[n.type]} fillOpacity={1} />
                      
                      <text y={n.isCluster ? 48 : 38} textAnchor="middle" fontSize={12} fill="#ffffff" fontWeight={isSelected ? 600 : 400} opacity={isSelected ? 1 : 0.85}>
                        {n.label}
                      </text>
                      {n.childCount && (
                        <text y={-3} textAnchor="middle" fontSize={10} fill="#ffffff" fontWeight={700} opacity={0.9}>
                          {n.childCount}
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
            </g>
          </svg>

          {/* Bottom Timeline Slider */}
          {globalTimeBounds && timeRange && (
            <div className="absolute bottom-4 left-4 right-4 border border-white/5 p-3 rounded-xl flex items-center gap-4 shadow-[0_8px_30px_rgb(0,0,0,0.3)]" style={{ background: "rgba(10,10,14,0.9)", backdropFilter: "blur(16px)" }}>
              <Clock className="h-3.5 w-3.5 text-muted-foreground/30 shrink-0" />
              <div className="flex-1 flex items-center gap-4">
                <span className="data-mono text-[10px] text-muted-foreground/30 whitespace-nowrap">{new Date(globalTimeBounds[0]).toLocaleDateString()}</span>
                <input 
                  type="range" 
                  min={globalTimeBounds[0]} 
                  max={globalTimeBounds[1]} 
                  value={timeRange[1]}
                  onChange={e => setTimeRange([globalTimeBounds[0], Number(e.target.value)])}
                  className="w-full accent-primary h-0.5 bg-white/5 rounded-lg appearance-none cursor-pointer"
                />
                <span className="data-mono text-[10px] text-primary/60 font-medium whitespace-nowrap">{new Date(timeRange[1]).toLocaleDateString()}</span>
              </div>
            </div>
          )}

          {/* Bottom Left Hover Info */}
          {hover && hover.evidenceData && !focusMap?.has(hover.id) && (
            <div className="pointer-events-none absolute bottom-20 left-4 z-10 max-w-xs rounded border border-border bg-card p-3 text-xs shadow-lg">
              <p className="font-semibold text-sm">{hover.label}</p>
              {hover.evidenceData.timestamp && <p className="text-muted-foreground mt-1">{hover.evidenceData.timestamp}</p>}
              {hover.evidenceData.confidence && <p className="mt-1 text-primary">{hover.evidenceData.confidence}% confidence</p>}
              {hover.evidenceData.preview && <p className="mt-2">{hover.evidenceData.preview}</p>}
            </div>
          )}

          <div className="absolute bottom-20 right-4 z-10 flex flex-col gap-0.5 rounded-xl border border-white/5 p-1 shadow-[0_4px_20px_rgb(0,0,0,0.3)]" style={{ background: "rgba(10,10,14,0.9)", backdropFilter: "blur(12px)" }}>
            <button onClick={() => {if(svgRef.current&&zoomRef.current) d3.select(svgRef.current).transition().call(zoomRef.current.scaleBy, 1.4)}} className="p-2 hover:bg-white/5 rounded-lg text-foreground/40 hover:text-foreground/70 transition-colors"><ZoomIn className="h-3.5 w-3.5" /></button>
            <button onClick={() => {if(svgRef.current&&zoomRef.current) d3.select(svgRef.current).transition().call(zoomRef.current.scaleBy, 0.7)}} className="p-2 hover:bg-white/5 rounded-lg text-foreground/40 hover:text-foreground/70 transition-colors"><ZoomOut className="h-3.5 w-3.5" /></button>
            <button onClick={() => {if(svgRef.current&&zoomRef.current) d3.select(svgRef.current).transition().call(zoomRef.current.transform, d3.zoomIdentity)}} className="p-2 hover:bg-white/5 rounded-lg text-foreground/40 hover:text-foreground/70 transition-colors"><Maximize2 className="h-3.5 w-3.5" /></button>
          </div>
        </div>

        {/* Right Detail Panel */}
        {selected && (
          <aside
            className="w-72 border-l border-white/5 flex flex-col shrink-0 backdrop-blur-xl"
            style={{ background: "linear-gradient(180deg, #0a0a0d 0%, #0c0c10 100%)" }}
          >
            <div className="flex items-start justify-between border-b border-white/5 p-4">
              <div className="flex items-start gap-3">
                <div className="h-8 w-8 rounded-lg flex items-center justify-center border" style={{ background: `${typeColor[selected.type]}12`, color: typeColor[selected.type], borderColor: `${typeColor[selected.type]}25` }}>
                  {(() => { const Icon = typeIcon[selected.type]; return <Icon className="h-3.5 w-3.5" />; })()}
                </div>
                <div>
                  <p className="text-[9px] uppercase tracking-[0.2em] text-muted-foreground/35">{selected.type}</p>
                  <h3 className="text-[14px] font-medium leading-tight mt-0.5 text-foreground/85">{selected.label}</h3>
                  {selected.reliability && <p className="text-[11px] text-muted-foreground/35 mt-0.5">{selected.reliability}</p>}
                </div>
              </div>
              <button onClick={() => setSelected(null)} className="p-1.5 hover:bg-white/5 rounded-lg text-muted-foreground/30 hover:text-foreground/60 transition-colors"><X className="h-3.5 w-3.5" /></button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-4 text-sm">
              {selected.isCluster && (
                 <div className="p-3 bg-primary/10 border border-primary/20 rounded text-primary text-xs">
                   This is a Macro-Node clustering {selected.childCount} entities of type {selected.type}. Toggle off Macro Clustering to see individual entities.
                 </div>
              )}

              {selected.evidenceData ? (
                <>
                  {selected.evidenceData.timestamp && <Field label="Timestamp" value={selected.evidenceData.timestamp} />}
                  {selected.evidenceData.location && <Field label="Location" value={selected.evidenceData.location} />}
                  {selected.evidenceData.confidence !== undefined && (
                    <div>
                      <p className="text-xs uppercase tracking-widest text-muted-foreground">Confidence</p>
                      <div className="mt-1 flex items-center gap-2">
                        <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                          <div className="h-full bg-primary" style={{ width: `${selected.evidenceData.confidence}%` }} />
                        </div>
                        <span className="text-xs text-primary font-medium">{selected.evidenceData.confidence}%</span>
                      </div>
                    </div>
                  )}
                  {selected.evidenceData.preview && <Field label="Preview" value={selected.evidenceData.preview} />}
                  {selected.evidenceData.details && (
                    <div>
                      <p className="text-xs uppercase tracking-widest text-muted-foreground">Details</p>
                      <p className="mt-1 leading-relaxed text-muted-foreground">{selected.evidenceData.details}</p>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-muted-foreground italic text-xs">No detailed evidence attached to this node.</p>
              )}

              <div className="pt-4 border-t border-border">
                <p className="text-xs uppercase tracking-widest text-muted-foreground mb-2">Direct Connections</p>
                <ul className="space-y-1">
                  {visibleEdges.filter((e) => e.source.id === selected.id || e.target.id === selected.id).map((e, i) => {
                    const other = e.source.id === selected.id ? e.target : e.source;
                    if (!other) return null;
                    return (
                      <li key={i}>
                        <button
                          onClick={() => handleSelect(other)}
                          className="w-full text-left rounded border border-border bg-background px-3 py-2 text-xs hover:border-primary/50 hover:bg-muted transition-colors flex items-center justify-between"
                        >
                          <span className="font-medium truncate mr-2">{other.label}</span>
                          <span className="text-muted-foreground whitespace-nowrap text-[10px] uppercase">{e.label ?? "linked"}</span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-widest text-muted-foreground">{label}</p>
      <p className="mt-1 font-medium">{value}</p>
    </div>
  );
}
