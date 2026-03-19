"use client"

import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type ReactFlowInstance,
  useEdgesState,
  useNodesState,
} from "@xyflow/react"
import { Focus, Maximize2, Minimize2, Network } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { getSessionDetail } from "@/lib/api/history"
import type { MindMapData, MindMapEdge, MindMapNode } from "@/types"

import { CustomNode } from "./CustomNode"

interface MindMapViewerProps {
  sessionId: string
  initialData?: MindMapData | null
}

const nodeTypes = {
  root: CustomNode,
  main: CustomNode,
  sub: CustomNode,
}

export function MindMapViewer({ sessionId, initialData }: MindMapViewerProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<MindMapNode>(
    initialData?.nodes ?? []
  )
  const [edges, setEdges, onEdgesChange] = useEdgesState<MindMapEdge>(
    initialData?.edges ?? []
  )
  const [graphData, setGraphData] = useState<MindMapData | null>(initialData ?? null)
  const [selectedNode, setSelectedNode] = useState<MindMapNode | null>(null)
  const [expandedNodeIds, setExpandedNodeIds] = useState<string[]>([])
  const [flowInstance, setFlowInstance] =
    useState<ReactFlowInstance<MindMapNode, MindMapEdge> | null>(null)
  const [loading, setLoading] = useState(!(initialData?.nodes?.length))
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!initialData?.nodes?.length) {
      return
    }

    setGraphData(initialData)
    setSelectedNode(initialData.nodes.find((node) => node.type === "root") ?? initialData.nodes[0] ?? null)
    setExpandedNodeIds([])
    setLoading(false)
    setError(null)
  }, [initialData])

  useEffect(() => {
    let isMounted = true

    async function loadMindMap() {
      if (initialData?.nodes?.length) {
        return
      }

      setLoading(true)
      setError(null)

      try {
        const response = await getSessionDetail(sessionId)
        const mindmapData = response.session?.mindmap_data

        if (!isMounted) {
          return
        }

        if (mindmapData?.nodes?.length) {
          setGraphData(mindmapData)
          setSelectedNode(
            mindmapData.nodes.find((node) => node.type === "root") ??
              mindmapData.nodes[0] ??
              null
          )
          setExpandedNodeIds([])
          return
        }

        setGraphData({ nodes: [], edges: [] })
        setError("Mind map chưa có dữ liệu để hiển thị.")
      } catch {
        if (isMounted) {
          setError("Không thể tải mind map lúc này.")
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    void loadMindMap()

    return () => {
      isMounted = false
    }
  }, [initialData, sessionId])

  useEffect(() => {
    if (!graphData) {
      return
    }

    const visibleGraph = buildVisibleGraph(graphData, expandedNodeIds)
    setNodes(visibleGraph.nodes)
    setEdges(visibleGraph.edges)
  }, [expandedNodeIds, graphData, setEdges, setNodes])

  useEffect(() => {
    if (!flowInstance || !nodes.length) {
      return
    }

    const timeout = window.setTimeout(() => {
      flowInstance.fitView({ padding: 0.24, duration: 250 })
    }, 60)

    return () => window.clearTimeout(timeout)
  }, [expandedNodeIds, flowInstance, nodes.length])

  const miniMapNodeColor = useMemo(
    () => (node: MindMapNode) => {
      if (node.type === "root") {
        return "#0f766e"
      }
      return node.data.color || "#94a3b8"
    },
    []
  )

  const hasExpandableChildren = Boolean(
    selectedNode && graphData?.edges.some((edge) => edge.source === selectedNode.id)
  )

  if (loading) {
    return (
      <Card className="border border-border/70 bg-card/90">
        <CardContent className="flex h-[560px] items-center justify-center text-sm text-muted-foreground">
          Đang tải mind map...
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border border-border/70 bg-card/90">
        <CardContent className="flex h-[560px] items-center justify-center text-sm text-muted-foreground">
          {error}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {selectedNode ? (
        <Card className="border border-border/70 bg-card/92">
          <CardContent className="space-y-4 p-5">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.2em] text-primary">
                  <Network className="size-3.5" />
                  Chi tiết node
                </div>
                <h4 className="font-display text-xl font-semibold text-balance">
                  {(selectedNode.data.full_label as string) ||
                    selectedNode.data.label}
                </h4>
                {selectedNode.data.description ? (
                  <p className="text-sm leading-6 text-foreground/80">
                    {selectedNode.data.description as string}
                  </p>
                ) : null}
                {selectedNode.data.details ? (
                  <p className="text-sm leading-6 text-muted-foreground">
                    {selectedNode.data.details as string}
                  </p>
                ) : null}
              </div>

              <div className="flex flex-wrap gap-2">
                {hasExpandableChildren ? (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => toggleNodeExpansion(selectedNode.id, setExpandedNodeIds)}
                  >
                    {expandedNodeIds.includes(selectedNode.id) ? (
                      <>
                        <Minimize2 className="mr-2 size-4" />
                        Thu gọn nhánh
                      </>
                    ) : (
                      <>
                        <Maximize2 className="mr-2 size-4" />
                        Mở rộng nhánh
                      </>
                    )}
                  </Button>
                ) : null}

                <Button
                  type="button"
                  variant="outline"
                  onClick={() => flowInstance?.fitView({ padding: 0.24, duration: 250 })}
                >
                  <Focus className="mr-2 size-4" />
                  Căn lại sơ đồ
                </Button>
              </div>
            </div>

            <p className="text-xs text-muted-foreground">
              Nhấn vào từng nhánh trong sơ đồ để xem đầy đủ nội dung. Với nhánh
              chính, bạn có thể mở rộng để hiện thêm các nhánh con nếu dữ liệu có sẵn.
            </p>
          </CardContent>
        </Card>
      ) : null}

      <div className="h-[560px] overflow-hidden rounded-2xl border border-border/70 bg-[linear-gradient(180deg,_rgba(240,253,250,0.9),_rgba(248,250,252,0.98))]">
        <ReactFlow<MindMapNode, MindMapEdge>
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={(_, node) => {
            setSelectedNode(node)
            if (graphData?.edges.some((edge) => edge.source === node.id)) {
              toggleNodeExpansion(node.id, setExpandedNodeIds)
            }
          }}
          onInit={setFlowInstance}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.24 }}
          proOptions={{ hideAttribution: true }}
          className="bg-transparent"
        >
          <Background color="#d9e3e1" gap={18} />
          <Controls />
          <MiniMap<MindMapNode> zoomable pannable nodeColor={miniMapNodeColor} />
        </ReactFlow>
      </div>
    </div>
  )
}

function toggleNodeExpansion(
  nodeId: string,
  setExpandedNodeIds: React.Dispatch<React.SetStateAction<string[]>>
) {
  setExpandedNodeIds((current) => {
    if (current.includes(nodeId)) {
      return current.filter((id) => id !== nodeId)
    }
    return [...current, nodeId]
  })
}

function buildVisibleGraph(graphData: MindMapData, expandedNodeIds: string[]) {
  const expandedSet = new Set(expandedNodeIds)
  const visibleNodeIds = new Set<string>()

  graphData.nodes.forEach((node) => {
    if (node.type === "root" || node.type === "main") {
      visibleNodeIds.add(node.id)
    }
  })

  graphData.nodes.forEach((node) => {
    if (node.type !== "sub") {
      return
    }

    const parentIds = graphData.edges
      .filter((edge) => edge.target === node.id)
      .map((edge) => edge.source)

    if (parentIds.some((parentId) => expandedSet.has(parentId))) {
      visibleNodeIds.add(node.id)
    }
  })

  return {
    nodes: graphData.nodes.map((node) => ({
      ...node,
      hidden: !visibleNodeIds.has(node.id),
    })),
    edges: graphData.edges.map((edge) => ({
      ...edge,
      hidden:
        !visibleNodeIds.has(edge.source) || !visibleNodeIds.has(edge.target),
    })),
  }
}
