using System;

namespace Edict.Core;

/// <summary>
/// 固定步长模拟时钟。逻辑每秒 10 次，与渲染帧率解耦。
/// </summary>
public sealed class SimClock
{
    public const double TicksPerSecond = 10.0;
    public const double TickSeconds = 1.0 / TicksPerSecond;

    /// <summary>单帧最多补的 tick 数，防止卡顿后雪崩。</summary>
    private const int MaxCatchUpTicks = 5;

    public long Tick { get; private set; }
    public double Speed { get; set; } = 1.0;

    private double _accumulator;

    /// <summary>0..1，本 tick 内的插值进度，渲染平滑用。</summary>
    public double Alpha => _accumulator / TickSeconds;

    public void Advance(double delta)
    {
        _accumulator += delta * Speed;
        int steps = 0;
        while (_accumulator >= TickSeconds && steps < MaxCatchUpTicks)
        {
            _accumulator -= TickSeconds;
            Tick++;
            steps++;
        }
        if (steps == MaxCatchUpTicks) _accumulator = 0;
    }

    public void Load(long tick)
    {
        Tick = tick;
        _accumulator = 0;
    }
}
