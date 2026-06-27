export interface Block {
  id: string
  row: number
  col: number
  size: number
  orientation: 'h' | 'v'
  color: string
  isTarget?: boolean
}

export interface Level {
  id: number
  name: string
  difficulty: 'Easy' | 'Medium' | 'Hard' | 'Expert'
  blocks: Block[]
}

export const levels: Level[] = [
  {
    id: 1,
    name: "Warm Up",
    difficulty: "Easy",
    blocks: [
      // Target red block (must exit at row 2, col 5)
      { id: 'target', row: 2, col: 1, size: 2, orientation: 'h', color: 'bg-rose-500 shadow-rose-500/50', isTarget: true },
      // Obstacles
      { id: 'v1', row: 0, col: 3, size: 2, orientation: 'v', color: 'bg-teal-500 shadow-teal-500/30' },
      { id: 'v2', row: 3, col: 0, size: 3, orientation: 'v', color: 'bg-indigo-500 shadow-indigo-500/30' },
      { id: 'h1', row: 0, col: 0, size: 2, orientation: 'h', color: 'bg-amber-500 shadow-amber-500/30' },
      { id: 'h2', row: 4, col: 2, size: 2, orientation: 'h', color: 'bg-purple-500 shadow-purple-500/30' },
      { id: 'v3', row: 3, col: 4, size: 2, orientation: 'v', color: 'bg-cyan-500 shadow-cyan-500/30' },
    ]
  },
  {
    id: 2,
    name: "Traffic Jam",
    difficulty: "Easy",
    blocks: [
      { id: 'target', row: 2, col: 1, size: 2, orientation: 'h', color: 'bg-rose-500 shadow-rose-500/50', isTarget: true },
      { id: 'v1', row: 0, col: 0, size: 2, orientation: 'v', color: 'bg-teal-500 shadow-teal-500/30' },
      { id: 'v2', row: 0, col: 3, size: 3, orientation: 'v', color: 'bg-indigo-500 shadow-indigo-500/30' },
      { id: 'v3', row: 1, col: 4, size: 2, orientation: 'v', color: 'bg-cyan-500 shadow-cyan-500/30' },
      { id: 'h1', row: 0, col: 1, size: 2, orientation: 'h', color: 'bg-amber-500 shadow-amber-500/30' },
      { id: 'h2', row: 3, col: 1, size: 2, orientation: 'h', color: 'bg-purple-500 shadow-purple-500/30' },
      { id: 'h3', row: 5, col: 2, size: 3, orientation: 'h', color: 'bg-emerald-500 shadow-emerald-500/30' },
    ]
  },
  {
    id: 3,
    name: "Gridlock",
    difficulty: "Medium",
    blocks: [
      { id: 'target', row: 2, col: 1, size: 2, orientation: 'h', color: 'bg-rose-500 shadow-rose-500/50', isTarget: true },
      { id: 'v1', row: 0, col: 0, size: 3, orientation: 'v', color: 'bg-indigo-500 shadow-indigo-500/30' },
      { id: 'v2', row: 0, col: 5, size: 3, orientation: 'v', color: 'bg-cyan-500 shadow-cyan-500/30' },
      { id: 'v3', row: 3, col: 2, size: 2, orientation: 'v', color: 'bg-teal-500 shadow-teal-500/30' },
      { id: 'v4', row: 4, col: 3, size: 2, orientation: 'v', color: 'bg-emerald-500 shadow-emerald-500/30' },
      { id: 'h1', row: 0, col: 1, size: 3, orientation: 'h', color: 'bg-amber-500 shadow-amber-500/30' },
      { id: 'h2', row: 3, col: 3, size: 2, orientation: 'h', color: 'bg-purple-500 shadow-purple-500/30' },
      { id: 'h3', row: 5, col: 4, size: 2, orientation: 'h', color: 'bg-orange-500 shadow-orange-500/30' },
    ]
  },
  {
    id: 4,
    name: "Maze Runner",
    difficulty: "Hard",
    blocks: [
      { id: 'target', row: 2, col: 1, size: 2, orientation: 'h', color: 'bg-rose-500 shadow-rose-500/50', isTarget: true },
      { id: 'v1', row: 0, col: 0, size: 2, orientation: 'v', color: 'bg-teal-500 shadow-teal-500/30' },
      { id: 'v2', row: 0, col: 3, size: 2, orientation: 'v', color: 'bg-indigo-500 shadow-indigo-500/30' },
      { id: 'v3', row: 1, col: 4, size: 3, orientation: 'v', color: 'bg-cyan-500 shadow-cyan-500/30' },
      { id: 'v4', row: 3, col: 0, size: 2, orientation: 'v', color: 'bg-emerald-500 shadow-emerald-500/30' },
      { id: 'v5', row: 3, col: 3, size: 3, orientation: 'v', color: 'bg-violet-500 shadow-violet-500/30' },
      { id: 'h1', row: 0, col: 1, size: 2, orientation: 'h', color: 'bg-amber-500 shadow-amber-500/30' },
      { id: 'h2', row: 3, col: 1, size: 2, orientation: 'h', color: 'bg-purple-500 shadow-purple-500/30' },
      { id: 'h3', row: 5, col: 0, size: 3, orientation: 'h', color: 'bg-orange-500 shadow-orange-500/30' },
    ]
  },
  {
    id: 5,
    name: "The Bottleneck",
    difficulty: "Expert",
    blocks: [
      { id: 'target', row: 2, col: 1, size: 2, orientation: 'h', color: 'bg-rose-500 shadow-rose-500/50', isTarget: true },
      { id: 'v1', row: 0, col: 0, size: 3, orientation: 'v', color: 'bg-indigo-500 shadow-indigo-500/30' },
      { id: 'v2', row: 0, col: 3, size: 2, orientation: 'v', color: 'bg-teal-500 shadow-teal-500/30' },
      { id: 'v3', row: 1, col: 4, size: 2, orientation: 'v', color: 'bg-cyan-500 shadow-cyan-500/30' },
      { id: 'v4', row: 3, col: 0, size: 2, orientation: 'v', color: 'bg-emerald-500 shadow-emerald-500/30' },
      { id: 'v5', row: 3, col: 2, size: 3, orientation: 'v', color: 'bg-purple-500 shadow-purple-500/30' },
      { id: 'v6', row: 4, col: 5, size: 2, orientation: 'v', color: 'bg-pink-500 shadow-pink-500/30' },
      { id: 'h1', row: 0, col: 1, size: 2, orientation: 'h', color: 'bg-amber-500 shadow-amber-500/30' },
      { id: 'h2', row: 3, col: 3, size: 2, orientation: 'h', color: 'bg-orange-500 shadow-orange-500/30' },
      { id: 'h3', row: 5, col: 3, size: 2, orientation: 'h', color: 'bg-violet-500 shadow-violet-500/30' }
    ]
  }
]
