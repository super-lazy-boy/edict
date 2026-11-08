using System;
using System.Collections.Generic;

namespace Edict.Core;

/// <summary>
/// 市民系统。所有市民存在一个连续数组里，按固定步长推进。
/// 不依赖引擎——可以脱离画面跑 1000 倍速测试。
/// </summary>
public sealed class CitizenSystem
{
    public const float TileSize = 48f;

    private Citizen[] _citizens = Array.Empty<Citizen>();
    private int _count;

    private readonly Random _rng;
    private int _nextId = 1;

    public World World { get; private set; }
    public JobBoard Jobs { get; } = new();

    /// <summary>工作完成时回调（瓦片X, 瓦片Y, 类型）。建筑系统用它来标记完工。</summary>
    public Action<int, int, JobType>? OnJobDone;

    /// <summary>居民点中心（世界像素坐标）。</summary>
    public float HomeX { get; private set; }
    public float HomeY { get; private set; }

    public int Count => _count;
    public ReadOnlySpan<Citizen> Citizens => _citizens.AsSpan(0, _count);

    public CitizenSystem(World world, int seed)
    {
        World = world;
        _rng = new Random(seed);

        float cx = world.Width * TileSize * 0.5f;
        float cy = world.Height * TileSize * 0.5f;

        // 居民点必须落在陆地上——地图中心经常是湖
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
                    if (!World.InBounds(tx, ty)) continue;

                    var t = World[tx, ty];
                    if (t == TileType.Water || t == TileType.Rock || t == TileType.Void) continue;

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
        if (_citizens.Length < n) _citizens = new Citizen[Math.Max(n, 64)];
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
        };
        _citizens[_count++] = c;
    }

    /// <summary>把地图上的树变成砍伐工作。</summary>
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

    /// <summary>推进一个 tick。dt 固定为 0.1 秒。</summary>
    public void Tick(float dt)
    {
        for (int i = 0; i < _count; i++)
        {
            ref Citizen c = ref _citizens[i];
            UpdateNeeds(ref c, dt);
            UpdateBehaviour(ref c, dt);
        }
    }

    private void UpdateNeeds(ref Citizen c, float dt)
    {
        // 饥饿增长；干活时增长更快
        float hungerRate = c.State == CitizenState.Working ? 0.55f : 0.35f;
        c.Hunger = MathF.Min(100f, c.Hunger + hungerRate * dt);

        // 体力：干活掉，闲着回
        if (c.State == CitizenState.Working)
            c.Energy = MathF.Max(0f, c.Energy - 0.8f * dt);
        else
            c.Energy = MathF.Min(100f, c.Energy + 0.25f * dt);

        // 心情：饿和累都掉心情
        float moodTarget = 70f - c.Hunger * 0.4f - (100f - c.Energy) * 0.2f;
        c.Mood += (moodTarget - c.Mood) * 0.02f;
        c.Mood = Math.Clamp(c.Mood, 0f, 100f);
    }

    private void UpdateBehaviour(ref Citizen c, float dt)
    {
        // 1. 太饿就先去吃
        if (c.Hunger > 80f && c.State != CitizenState.Eating)
        {
            ReleaseJob(ref c);
            c.State = CitizenState.Eating;
        }

        switch (c.State)
        {
            case CitizenState.Eating:
                c.Hunger = MathF.Max(0f, c.Hunger - 12f * dt);
                if (c.Hunger <= 10f) c.State = CitizenState.Idle;
                break;

            case CitizenState.Idle:
                if (!TryTakeJob(ref c))
                    StartWander(ref c);
                break;

            case CitizenState.Moving:
                TryMove(ref c, dt);
                if (Near(c, c.TargetX, c.TargetY, 6f))
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

    private bool TryTakeJob(ref Citizen c)
    {
        int idx = Jobs.Claim(c.Id, c.X, c.Y);
        if (idx < 0) return false;

        var j = Jobs.Jobs[idx];
        c.JobId = idx;
        c.Job = j.Type;
        c.TargetX = j.X;
        c.TargetY = j.Y;
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

        if (j.Remaining <= 0f)
        {
            // 树被砍倒：地图上的森林变成草地
            if (j.Type == JobType.ChopTree && World[j.TileX, j.TileY] == TileType.Forest)
                World.SetTile(j.TileX, j.TileY, TileType.Grass);

            Jobs.Complete(c.JobId);
            OnJobDone?.Invoke(j.TileX, j.TileY, j.Type);
            c.JobId = -1;
            c.Job = JobType.None;
            c.State = CitizenState.Idle;
            c.Energy = MathF.Max(0f, c.Energy - 3f);
        }
    }

    private void StartWander(ref Citizen c)
    {
        for (int tries = 0; tries < 12; tries++)
        {
            float ang = (float)(_rng.NextDouble() * Math.PI * 2);
            float rad = (float)(_rng.NextDouble() * 6 * TileSize);
            float tx = c.X + MathF.Cos(ang) * rad;
            float ty = c.Y + MathF.Sin(ang) * rad;
            if (IsWalkable(tx, ty))
            {
                c.TargetX = tx;
                c.TargetY = ty;
                c.State = CitizenState.Moving;
                return;
            }
        }
        c.State = CitizenState.Idle;
    }

    /// <summary>朝目标移动一步。撞到水面/岩石就放弃当前目标，重新找路。</summary>
    private void TryMove(ref Citizen c, float dt)
    {
        float dx = c.TargetX - c.X;
        float dy = c.TargetY - c.Y;
        float dist = MathF.Sqrt(dx * dx + dy * dy);
        if (dist < 0.001f) return;

        float step = c.Speed * dt;
        float nx, ny;
        if (step >= dist)
        {
            nx = c.TargetX;
            ny = c.TargetY;
        }
        else
        {
            nx = c.X + dx / dist * step;
            ny = c.Y + dy / dist * step;
        }

        if (!IsWalkable(nx, ny))
        {
            c.State = CitizenState.Idle;
            return;
        }

        c.X = nx;
        c.Y = ny;
    }

    private static bool Near(in Citizen c, float tx, float ty, float eps)
    {
        float dx = tx - c.X;
        float dy = ty - c.Y;
        return dx * dx + dy * dy <= eps * eps;
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
        var t = World[tx, ty];
        return t != TileType.Water && t != TileType.Rock && t != TileType.Void;
    }

    /// <summary>找到离给定世界坐标最近的市民，超出半径返回 -1。</summary>
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
