using System;
using System.Collections.Generic;

namespace Edict.Core;

/// <summary>
/// 市民系统。所有市民存在一个连续数组里，按固定步长推进。
/// 移动走 A* 路径，每 tick 有总节点预算，避免几百人同时寻路卡帧。
/// 不依赖引擎——可以脱离画面跑 1000 倍速测试。
/// </summary>
public sealed class CitizenSystem
{
    public const float TileSize = 48f;

    /// <summary>每 tick 全系统可用的寻路节点总数。超了就排队等下一 tick。</summary>
    public const int PathBudgetPerTick = 24000;

    /// <summary>游泳速度倍率。</summary>
    public const float SwimSpeedFactor = 0.4f;

    /// <summary>在水里每 tick 的溺水概率。0.0003 ≈ 每秒 0.3%，游 20 秒约 6%。</summary>
    public const double DrownChancePerTick = 0.0003;

    private Citizen[] _citizens = Array.Empty<Citizen>();
    private List<int>[] _paths = Array.Empty<List<int>>();
    private int _count;

    private readonly Random _rng;
    private int _nextId = 1;

    private int _pathBudgetLeft;

    public World World { get; private set; }
    public JobBoard Jobs { get; } = new();
    public Pathfinder Pathfinder { get; private set; } = null!;

    /// <summary>工作完成时回调（瓦片X, 瓦片Y, 类型）。建筑系统用它来标记完工。</summary>
    public Action<int, int, JobType>? OnJobDone;

    public float HomeX { get; private set; }
    public float HomeY { get; private set; }

    public int Count => _count;
    public ReadOnlySpan<Citizen> Citizens => _citizens.AsSpan(0, _count);

    /// <summary>本 tick 实际消耗的寻路节点数，用于性能观测。</summary>
    public int PathNodesUsed { get; private set; }

    public CitizenSystem(World world, int seed)
    {
        World = world;
        _rng = new Random(seed);
        Pathfinder = new Pathfinder(world);

        float cx = world.Width * TileSize * 0.5f;
        float cy = world.Height * TileSize * 0.5f;

        if (FindNearestWalkable(cx, cy, out float hx, out float hy))
        {
            HomeX = hx;
            HomeY = hy;
        }
        else
        {
            HomeX = cx;
            HomeY = cy;
        }
    }

    private bool FindNearestWalkable(float wx, float wy, out float rx, out float ry)
    {
        int ctx = (int)(wx / TileSize);
        int cty = (int)(wy / TileSize);

        for (int radius = 0; radius < Math.Max(World.Width, World.Height); radius++)
        {
            for (int dy = -radius; dy <= radius; dy++)
            {
                for (int dx = -radius; dx <= radius; dx++)
                {
                    if (Math.Abs(dx) != radius && Math.Abs(dy) != radius) continue;

                    int tx = ctx + dx, ty = cty + dy;
                    if (!Pathfinder.Walkable(tx, ty)) continue;

                    rx = tx * TileSize + TileSize * 0.5f;
                    ry = ty * TileSize + TileSize * 0.5f;
                    return true;
                }
            }
        }

        rx = wx;
        ry = wy;
        return false;
    }

    // ---------------- 生成 ----------------

    public void Spawn(int n)
    {
        if (_citizens.Length < n)
        {
            _citizens = new Citizen[Math.Max(n, 64)];
            _paths = new List<int>[Math.Max(n, 64)];
        }

        _count = 0;
        _nextId = 1;
        Jobs.Clear();

        for (int i = 0; i < n; i++) AddOne();
        GenerateJobs();
    }

    private void AddOne()
    {
        float x = HomeX, y = HomeY;
        for (int tries = 0; tries < 400; tries++)
        {
            float ang = (float)(_rng.NextDouble() * Math.PI * 2);
            float rad = (float)(_rng.NextDouble() * 8 * TileSize);
            float tx = HomeX + MathF.Cos(ang) * rad;
            float ty = HomeY + MathF.Sin(ang) * rad;
            if (IsWalkable(tx, ty))
            {
                x = tx;
                y = ty;
                break;
            }
        }

        var c = new Citizen
        {
            Id = _nextId++,
            X = x,
            Y = y,
            TargetX = x,
            TargetY = y,
            State = CitizenState.Idle,
            Job = JobType.None,
            JobId = -1,
            Hunger = (float)(_rng.NextDouble() * 30),
            Energy = 60f + (float)(_rng.NextDouble() * 40),
            Mood = 50f + (float)(_rng.NextDouble() * 30),
            Speed = 42f + (float)(_rng.NextDouble() * 18),
            Profession = (Profession)_rng.Next(0, 6),
            NameIndex = _rng.Next(0, 240),
            HasPath = 0,
            PathIndex = 0,
            Alive = 1,
        };
        _citizens[_count++] = c;
    }

    private void GenerateJobs()
    {
        int added = 0;
        for (int ty = 0; ty < World.Height && added < 240; ty++)
        {
            for (int tx = 0; tx < World.Width && added < 240; tx++)
            {
                if (World[tx, ty] != TileType.Forest) continue;
                if (_rng.Next(0, 3) != 0) continue;

                Jobs.Add(JobType.ChopTree, tx, ty,
                    tx * TileSize + TileSize * 0.5f,
                    ty * TileSize + TileSize * 0.5f,
                    4.0f);
                added++;
            }
        }
    }

    // ---------------- 推进 ----------------

    public void Tick(float dt)
    {
        _pathBudgetLeft = PathBudgetPerTick;
        PathNodesUsed = 0;

        for (int i = 0; i < _count; i++)
        {
            if (_citizens[i].Alive == 0) continue;
            ref Citizen c = ref _citizens[i];
            UpdateNeeds(ref c, dt);
            UpdateBehaviour(i, ref c, dt);
        }
    }

    public int AliveCount
    {
        get
        {
            int n = 0;
            for (int i = 0; i < _count; i++) if (_citizens[i].Alive != 0) n++;
            return n;
        }
    }

    public int DrownedCount { get; private set; }

    private void UpdateNeeds(ref Citizen c, float dt)
    {
        float hungerRate = c.State == CitizenState.Working ? 0.55f : 0.35f;
        c.Hunger = MathF.Min(100f, c.Hunger + hungerRate * dt);

        if (c.State == CitizenState.Working)
            c.Energy = MathF.Max(0f, c.Energy - 0.8f * dt);
        else
            c.Energy = MathF.Min(100f, c.Energy + 0.25f * dt);

        float moodTarget = 70f - c.Hunger * 0.4f - (100f - c.Energy) * 0.2f;
        c.Mood += (moodTarget - c.Mood) * 0.02f;
        c.Mood = Math.Clamp(c.Mood, 0f, 100f);
    }

    private void UpdateBehaviour(int i, ref Citizen c, float dt)
    {
        if (c.Hunger > 80f && c.State != CitizenState.Eating)
        {
            ReleaseJob(ref c);
            c.State = CitizenState.Eating;
            c.HasPath = 0;
        }

        switch (c.State)
        {
            case CitizenState.Eating:
                c.Hunger = MathF.Max(0f, c.Hunger - 12f * dt);
                if (c.Hunger <= 10f) c.State = CitizenState.Idle;
                break;

            case CitizenState.Idle:
                if (!TryTakeJob(i, ref c))
                    StartWander(i, ref c);
                break;

            case CitizenState.Moving:
                if (FollowPath(i, ref c, dt))
                {
                    if (c.JobId >= 0)
                    {
                        c.State = CitizenState.Working;
                        c.WorkTimer = 0f;
                    }
                    else
                    {
                        c.State = CitizenState.Idle;
                    }
                }
                break;

            case CitizenState.Working:
                WorkTick(ref c, dt);
                break;
        }
    }

    private bool TryTakeJob(int i, ref Citizen c)
    {
        int idx = Jobs.Claim(c.Id, c.X, c.Y);
        if (idx < 0) return false;

        var j = Jobs.Get(idx);
        c.JobId = idx;
        c.Job = j.Type;

        if (!RequestPath(i, ref c, j.X, j.Y))
        {
            Jobs.Release(idx);
            c.JobId = -1;
            c.Job = JobType.None;
            return false;
        }

        c.State = CitizenState.Moving;
        return true;
    }

    private void WorkTick(ref Citizen c, float dt)
    {
        if (c.JobId < 0)
        {
            c.State = CitizenState.Idle;
            return;
        }

        c.WorkTimer += dt;
        var j = Jobs.Get(c.JobId);
        Jobs.SetRemaining(c.JobId, j.Remaining - dt);

        if (j.Remaining - dt <= 0f)
        {
            if (j.Type == JobType.ChopTree && World[j.TileX, j.TileY] == TileType.Forest)
                World.SetTile(j.TileX, j.TileY, TileType.Grass);

            Jobs.Complete(c.JobId);
            OnJobDone?.Invoke(j.TileX, j.TileY, j.Type);
            c.JobId = -1;
            c.Job = JobType.None;
            c.State = CitizenState.Idle;
            c.HasPath = 0;
            c.Energy = MathF.Max(0f, c.Energy - 3f);
        }
    }

    private void StartWander(int i, ref Citizen c)
    {
        for (int tries = 0; tries < 10; tries++)
        {
            float ang = (float)(_rng.NextDouble() * Math.PI * 2);
            float rad = (float)(_rng.NextDouble() * 6 * TileSize);
            float tx = c.X + MathF.Cos(ang) * rad;
            float ty = c.Y + MathF.Sin(ang) * rad;
            if (!IsWalkable(tx, ty)) continue;

            if (RequestPath(i, ref c, tx, ty))
            {
                c.State = CitizenState.Moving;
                return;
            }
        }
        c.State = CitizenState.Idle;
    }

    // ---------------- 路径 ----------------

    private bool RequestPath(int i, ref Citizen c, float tx, float ty)
    {
        c.TargetX = tx;
        c.TargetY = ty;
        c.PathIndex = 0;
        c.HasPath = 0;

        if (_pathBudgetLeft <= 0) return false;

        int sx = (int)(c.X / TileSize);
        int sy = (int)(c.Y / TileSize);
        int gx = (int)(tx / TileSize);
        int gy = (int)(ty / TileSize);

        var list = _paths[i] ??= new List<int>(64);

        int budget = Math.Min(3000, _pathBudgetLeft);
        bool ok = Pathfinder.Find(sx, sy, gx, gy, list, budget);
        _pathBudgetLeft -= Pathfinder.LastExpanded;
        PathNodesUsed += Pathfinder.LastExpanded;

        if (!ok) return false;

        c.HasPath = 1;
        return true;
    }

    /// <summary>沿路径走一步。返回 true 表示已到达终点。</summary>
    private bool FollowPath(int i, ref Citizen c, float dt)
    {
        if (c.HasPath == 0) return true;

        var path = _paths[i];
        if (path == null || path.Count == 0) return true;
        if (c.PathIndex >= path.Count) return true;

        int tile = path[c.PathIndex];
        float wx = (tile % World.Width + 0.5f) * TileSize;
        float wy = (tile / World.Width + 0.5f) * TileSize;

        float dx = wx - c.X;
        float dy = wy - c.Y;
        float dist = MathF.Sqrt(dx * dx + dy * dy);

        // 在水里游得慢
        float speed = c.Speed;
        int ctx = (int)(c.X / TileSize);
        int cty = (int)(c.Y / TileSize);
        bool inWater = World[ctx, cty] == TileType.Water;
        bool safeWater = World.IsFerryWater(ctx, cty);
        if (inWater && !safeWater) speed *= SwimSpeedFactor;

        float step = speed * dt;

        if (step >= dist)
        {
            c.X = wx;
            c.Y = wy;
            c.PathIndex++;
            CheckDrown(ref c, wx, wy);
            return c.PathIndex >= path.Count;
        }

        c.X += dx / dist * step;
        c.Y += dy / dist * step;
        CheckDrown(ref c, c.X, c.Y);
        return false;
    }

    /// <summary>踩到没有渡口的水域就有溺水风险。</summary>
    private void CheckDrown(ref Citizen c, float x, float y)
    {
        if (c.Alive == 0) return;

        int tx = (int)(x / TileSize);
        int ty = (int)(y / TileSize);
        if (World[tx, ty] != TileType.Water) return;
        if (World.IsFerryWater(tx, ty)) return;

        if (_rng.NextDouble() < DrownChancePerTick)
        {
            c.Alive = 0;
            c.HasPath = 0;
            DrownedCount++;
            ReleaseJob(ref c);
        }
    }

    private void ReleaseJob(ref Citizen c)
    {
        if (c.JobId >= 0) Jobs.Release(c.JobId);
        c.JobId = -1;
        c.Job = JobType.None;
    }

    // ---------------- 查询 ----------------

    public bool IsWalkable(float worldX, float worldY)
    {
        int tx = (int)(worldX / TileSize);
        int ty = (int)(worldY / TileSize);
        return Pathfinder.Walkable(tx, ty);
    }

    public int FindNearest(float worldX, float worldY, float maxDist)
    {
        int best = -1;
        float bestD = maxDist * maxDist;
        for (int i = 0; i < _count; i++)
        {
            float dx = _citizens[i].X - worldX;
            float dy = _citizens[i].Y - worldY;
            float d = dx * dx + dy * dy;
            if (d < bestD)
            {
                bestD = d;
                best = i;
            }
        }
        return best;
    }

    public ref Citizen At(int index) => ref _citizens[index];

    public void RepositionHome(float x, float y)
    {
        HomeX = x;
        HomeY = y;
    }
}
