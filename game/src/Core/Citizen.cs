namespace Edict.Core;

/// <summary>市民当前在干什么。</summary>
public enum CitizenState : byte
{
    Idle = 0,
    Moving = 1,
    Working = 2,
    Eating = 3,
}

/// <summary>工作类型。</summary>
public enum JobType : byte
{
    None = 0,
    ChopTree = 1,
    Haul = 2,
    Build = 3,
}

/// <summary>职业。决定服装颜色与工作偏好。</summary>
public enum Profession : byte
{
    Farmer = 0,
    Artisan = 1,
    Merchant = 2,
    Soldier = 3,
    Official = 4,
    Noble = 5,
}

/// <summary>
/// 一个市民。结构体，存在连续数组里——这是撑住几千人的前提。
/// 不要改成 class，也不要把渲染数据塞进来。
/// </summary>
public struct Citizen
{
    public int Id;

    public float X;
    public float Y;

    public float TargetX;
    public float TargetY;

    public CitizenState State;
    public JobType Job;
    public int JobId;

    public float WorkTimer;

    /// <summary>0 = 饱，100 = 快饿死。</summary>
    public float Hunger;

    /// <summary>0 = 精疲力尽，100 = 精神饱满。</summary>
    public float Energy;

    /// <summary>0 = 绝望，100 = 心满意足。</summary>
    public float Mood;

    public float Speed;
    public Profession Profession;

    public int NameIndex;
}
