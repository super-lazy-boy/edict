using System;
using System.Collections.Generic;

namespace Edict.Core;

/// <summary>
/// 网格 A* 寻路。四方向，曼哈顿启发式。
/// 用"时间戳"数组避免每次搜索清空整张表——这是能扛住几千人寻路的关键。
/// 每次调用有节点预算，超了就放弃，防止一帧卡死。
/// </summary>
public sealed class Pathfinder
{
    public const int StepCost = 10;

    /// <summary>游泳的通行代价是走路的 4 倍——所以 A* 会优先绕陆路。</summary>
    public const int SwimCost = 40;

    /// <summary>渡口航道代价：比陆地略贵，但比游泳便宜得多，且不淹死。</summary>
    public const int FerryCost = 12;

    public const int DefaultBudget = 3000;

    private readonly World _world;
    private readonly int _w;
    private readonly int _h;

    private readonly int[] _g;
    private readonly int[] _parent;
    private readonly int[] _stamp;
    private readonly PriorityQueue<int, int> _open = new();

    private int _curStamp;

    /// <summary>上一次搜索展开的节点数，用于性能观测。</summary>
    public int LastExpanded { get; private set; }

    public Pathfinder(World world)
    {
        _world = world;
        _w = world.Width;
        _h = world.Height;
        int n = _w * _h;
        _g = new int[n];
        _parent = new int[n];
        _stamp = new int[n];
    }

    public bool Walkable(int tx, int ty)
    {
        if (tx < 0 || ty < 0 || tx >= _w || ty >= _h) return false;
        var t = _world[tx, ty];
        // 水可以游过去，只是又慢又危险
        return t != TileType.Rock && t != TileType.Void;
    }

    /// <summary>进入某个瓦片的代价。陆地 10，游泳 40，渡口航道 12。</summary>
    public int CostAt(int tx, int ty)
    {
        if (_world[tx, ty] != TileType.Water) return StepCost;
        return _world.IsFerryWater(tx, ty) ? FerryCost : SwimCost;
    }

    /// <summary>
    /// 求从 (sx,sy) 到 (gx,gy) 的路径，结果写入 outPath（瓦片索引序列，不含起点）。
    /// 找不到或超出预算返回 false。
    /// </summary>
    public bool Find(int sx, int sy, int gx, int gy, List<int> outPath, int budget = DefaultBudget)
    {
        outPath.Clear();
        LastExpanded = 0;

        if (!Walkable(sx, sy) || !Walkable(gx, gy)) return false;
        if (sx == gx && sy == gy) return true;

        _curStamp++;
        _open.Clear();

        int start = sy * _w + sx;
        int goal = gy * _w + gx;

        _stamp[start] = _curStamp;
        _g[start] = 0;
        _parent[start] = -1;
        _open.Enqueue(start, Heuristic(sx, sy, gx, gy));

        int expanded = 0;

        while (_open.Count > 0)
        {
            if (expanded >= budget)
            {
                LastExpanded = expanded;
                return false;   // 超预算，放弃
            }

            int cur = _open.Dequeue();
            expanded++;

            if (cur == goal)
            {
                LastExpanded = expanded;
                Reconstruct(cur, outPath);
                return true;
            }

            int cx = cur % _w;
            int cy = cur / _w;
            int gCur = _g[cur];

            // 四方向
            TryRelax(cx + 1, cy, cur, gCur, gx, gy);
            TryRelax(cx - 1, cy, cur, gCur, gx, gy);
            TryRelax(cx, cy + 1, cur, gCur, gx, gy);
            TryRelax(cx, cy - 1, cur, gCur, gx, gy);
        }

        LastExpanded = expanded;
        return false;
    }

    private void TryRelax(int nx, int ny, int parent, int gParent, int gx, int gy)
    {
        if (!Walkable(nx, ny)) return;

        int idx = ny * _w + nx;
        int ng = gParent + CostAt(nx, ny);

        if (_stamp[idx] == _curStamp && _g[idx] <= ng) return;

        _stamp[idx] = _curStamp;
        _g[idx] = ng;
        _parent[idx] = parent;
        _open.Enqueue(idx, ng + Heuristic(nx, ny, gx, gy));
    }

    private void Reconstruct(int goal, List<int> outPath)
    {
        var stack = new Stack<int>(64);
        int cur = goal;
        int guard = 0;

        while (cur >= 0 && guard++ < _w * _h)
        {
            stack.Push(cur);
            cur = _parent[cur];
        }

        // 去掉起点
        if (stack.Count > 0) stack.Pop();
        while (stack.Count > 0) outPath.Add(stack.Pop());
    }

    private static int Heuristic(int x, int y, int gx, int gy)
        => (Math.Abs(x - gx) + Math.Abs(y - gy)) * StepCost;
}
