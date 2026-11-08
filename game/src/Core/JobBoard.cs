using System.Collections.Generic;

namespace Edict.Core;

public struct Job
{
    public int Id;
    public JobType Type;
    public float X;
    public float Y;
    public int TileX;
    public int TileY;
    public float Work;
    public float Remaining;
    public int ClaimedBy;
    public bool Done;
}

/// <summary>
/// 全局工作板。市民空闲了来揭榜，揭了就占住，别人不能抢。
/// 贵族日后"指挥建设"，本质上就是往这块板子上插活、调优先级。
/// </summary>
public sealed class JobBoard
{
    public const int Nobody = -1;

    private readonly List<Job> _jobs = new();
    private int _nextId = 1;

    public IReadOnlyList<Job> Jobs => _jobs;

    public Job Get(int index) => _jobs[index];

    public void SetRemaining(int index, float remaining)
    {
        if (index < 0 || index >= _jobs.Count) return;
        var j = _jobs[index];
        j.Remaining = remaining;
        _jobs[index] = j;
    }

    public int Add(JobType type, int tileX, int tileY, float worldX, float worldY, float work)
    {
        var j = new Job
        {
            Id = _nextId++,
            Type = type,
            TileX = tileX,
            TileY = tileY,
            X = worldX,
            Y = worldY,
            Work = work,
            Remaining = work,
            ClaimedBy = Nobody,
            Done = false,
        };
        _jobs.Add(j);
        return _jobs.Count - 1;
    }

    /// <summary>找一份没被占的活，占住并返回索引；没有则返回 -1。</summary>
    public int Claim(int citizenId, float fromX, float fromY, int maxScan = 40)
    {
        int best = -1;
        float bestDist = float.MaxValue;

        int scanned = 0;
        for (int i = 0; i < _jobs.Count && scanned < maxScan; i++)
        {
            var j = _jobs[i];
            if (j.Done || j.ClaimedBy != Nobody) continue;
            scanned++;

            float dx = j.X - fromX;
            float dy = j.Y - fromY;
            float d = dx * dx + dy * dy;
            if (d < bestDist)
            {
                bestDist = d;
                best = i;
            }
        }

        if (best >= 0)
        {
            var j = _jobs[best];
            j.ClaimedBy = citizenId;
            _jobs[best] = j;
        }
        return best;
    }

    public void Release(int index)
    {
        if (index < 0 || index >= _jobs.Count) return;
        var j = _jobs[index];
        j.ClaimedBy = Nobody;
        _jobs[index] = j;
    }

    public void Complete(int index)
    {
        if (index < 0 || index >= _jobs.Count) return;
        var j = _jobs[index];
        j.Done = true;
        j.ClaimedBy = Nobody;
        _jobs[index] = j;
    }

    public int PendingCount
    {
        get
        {
            int n = 0;
            for (int i = 0; i < _jobs.Count; i++)
                if (!_jobs[i].Done) n++;
            return n;
        }
    }

    public int DoneCount
    {
        get
        {
            int n = 0;
            for (int i = 0; i < _jobs.Count; i++)
                if (_jobs[i].Done) n++;
            return n;
        }
    }

    public void Clear() => _jobs.Clear();
}
