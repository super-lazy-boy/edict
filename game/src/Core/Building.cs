using System;
using System.Collections.Generic;

namespace Edict.Core;

public enum ResourceKind : byte
{
    None = 0,
    Wood = 1,
    Food = 2,
    Stone = 3,
}

public enum BuildingType : byte
{
    None = 0,
    House = 1,      // 民居
    Farm = 2,       // 农田
    Warehouse = 3,  // 仓库
    LumberCamp = 4, // 伐木场
}

public struct BuildingDef
{
    public BuildingType Type;
    public string NameKey;
    public byte Size;          // 边长（瓦片数）
    public float BuildWork;    // 需要的工时
    public int WoodCost;
    public ResourceKind Produces;
    public float RatePerSecond;
    public int StorageBonus;

    private static readonly BuildingDef[] All =
    {
        new() { Type = BuildingType.None,       NameKey = "",                    Size = 1, BuildWork = 0,  WoodCost = 0,  Produces = ResourceKind.None,  RatePerSecond = 0f,   StorageBonus = 0 },
        new() { Type = BuildingType.House,      NameKey = "BLD_HOUSE_NAME",      Size = 2, BuildWork = 12, WoodCost = 5,  Produces = ResourceKind.None,  RatePerSecond = 0f,   StorageBonus = 0 },
        new() { Type = BuildingType.Farm,       NameKey = "BLD_FARM_NAME",       Size = 3, BuildWork = 20, WoodCost = 8,  Produces = ResourceKind.Food,  RatePerSecond = 0.6f, StorageBonus = 0 },
        new() { Type = BuildingType.Warehouse,  NameKey = "BLD_WAREHOUSE_NAME",  Size = 3, BuildWork = 24, WoodCost = 12, Produces = ResourceKind.None,  RatePerSecond = 0f,   StorageBonus = 200 },
        new() { Type = BuildingType.LumberCamp, NameKey = "BLD_LUMBERCAMP_NAME", Size = 2, BuildWork = 16, WoodCost = 6,  Produces = ResourceKind.Wood,  RatePerSecond = 0.5f, StorageBonus = 0 },
    };

    public static BuildingDef Get(BuildingType t) => All[(int)t];
    public static BuildingDef[] List() => All;
}

/// <summary>地图上的一座建筑。</summary>
public struct Building
{
    public int Id;
    public BuildingType Type;
    public int TileX;
    public int TileY;
    public byte Size;

    public bool Complete;
    public float BuildProgress;
    public float BuildWorkDone;

    /// <summary>生产建筑攒下来的产出，等待搬运。</summary>
    public float Buffer;
}

/// <summary>全局资源。仓库提供容量。</summary>
public sealed class Stockpile
{
    public float Wood;
    public float Food;
    public float Stone;
    public int Capacity = 300;

    public float Total => Wood + Food + Stone;
    public bool IsFull => Total >= Capacity;

    public bool TrySpendWood(int amount)
    {
        if (Wood < amount) return false;
        Wood -= amount;
        return true;
    }

    public void Add(ResourceKind kind, float amount)
    {
        if (IsFull) return;
        float room = Capacity - Total;
        if (amount > room) amount = room;
        if (amount <= 0f) return;

        switch (kind)
        {
            case ResourceKind.Wood: Wood += amount; break;
            case ResourceKind.Food: Food += amount; break;
            case ResourceKind.Stone: Stone += amount; break;
        }
    }

    public float Of(ResourceKind kind) => kind switch
    {
        ResourceKind.Wood => Wood,
        ResourceKind.Food => Food,
        ResourceKind.Stone => Stone,
        _ => 0f,
    };
}

/// <summary>
/// 建筑系统：放置、建造、生产。
/// 生产速率受国风修正（农业/工业）影响。
/// </summary>
public sealed class BuildingSystem
{
    public const float TileSize = 48f;

    private readonly List<Building> _buildings = new();
    private int _nextId = 1;

    public World World { get; private set; }
    public JobBoard Jobs { get; }
    public Stockpile Stock { get; } = new();
    public CivDefinition Civ { get; set; } = CivDefinition.Get(CivId.Jixia);

    public IReadOnlyList<Building> Buildings => _buildings;
    public int Count => _buildings.Count;

    public BuildingSystem(World world, JobBoard jobs, CivId civ)
    {
        World = world;
        Jobs = jobs;
        Civ = CivDefinition.Get(civ);
    }

    // ---------------- 放置 ----------------

    public bool CanPlace(int tileX, int tileY, BuildingType type)
    {
        var def = BuildingDef.Get(type);
        int s = def.Size;

        for (int dy = 0; dy < s; dy++)
        {
            for (int dx = 0; dx < s; dx++)
            {
                int tx = tileX + dx, ty = tileY + dy;
                if (!World.InBounds(tx, ty)) return false;

                var t = World[tx, ty];
                if (t == TileType.Water || t == TileType.Rock || t == TileType.Void) return false;

                // 不允许重叠
                for (int i = 0; i < _buildings.Count; i++)
                {
                    var b = _buildings[i];
                    int bs = b.Size;
                    if (tx >= b.TileX && tx < b.TileX + bs && ty >= b.TileY && ty < b.TileY + bs)
                        return false;
                }
            }
        }
        return true;
    }

    public int Place(int tileX, int tileY, BuildingType type)
    {
        var def = BuildingDef.Get(type);
        if (!CanPlace(tileX, tileY, type)) return -1;

        var b = new Building
        {
            Id = _nextId++,
            Type = type,
            TileX = tileX,
            TileY = tileY,
            Size = def.Size,
            Complete = false,
            BuildProgress = 0f,
        };
        _buildings.Add(b);

        // 生成建造工作：工时按国风的建造速度修正
        float work = def.BuildWork / MathF.Max(0.2f, Civ.Mods.BuildSpeed);
        Jobs.Add(JobType.Build, tileX, tileY,
            (tileX + def.Size * 0.5f) * TileSize,
            (tileY + def.Size * 0.5f) * TileSize,
            work);

        return _buildings.Count - 1;
    }

    // ---------------- 推进 ----------------

    public void Tick(float dt)
    {
        RecomputeCapacity();

        for (int i = 0; i < _buildings.Count; i++)
        {
            var b = _buildings[i];
            if (!b.Complete) continue;

            var def = BuildingDef.Get(b.Type);
            if (def.Produces == ResourceKind.None) continue;

            float mult = def.Produces == ResourceKind.Food
                ? Civ.Mods.FarmOutput
                : Civ.Mods.IndustryOutput;

            b.Buffer += def.RatePerSecond * mult * dt;
            _buildings[i] = b;

            // 缓冲满了自动入库（M2 简化：不搬运，直接进全局库存）
            if (b.Buffer >= 1f)
            {
                Stock.Add(def.Produces, b.Buffer);
                b.Buffer = 0f;
                _buildings[i] = b;
            }
        }
    }

    private void RecomputeCapacity()
    {
        int cap = 300;
        for (int i = 0; i < _buildings.Count; i++)
        {
            var b = _buildings[i];
            if (!b.Complete) continue;
            cap += BuildingDef.Get(b.Type).StorageBonus;
        }
        Stock.Capacity = cap;
    }

    /// <summary>建造完成时由 CitizenSystem 调用。</summary>
    public void OnJobCompleted(int tileX, int tileY, JobType jobType)
    {
        if (jobType != JobType.Build) return;

        for (int i = 0; i < _buildings.Count; i++)
        {
            var b = _buildings[i];
            if (b.Complete) continue;
            if (b.TileX != tileX || b.TileY != tileY) continue;

            b.Complete = true;
            b.BuildProgress = 1f;
            _buildings[i] = b;
            return;
        }
    }

    public void Reset(World world, JobBoard jobs)
    {
        _buildings.Clear();
        _nextId = 1;
        World = world;
        Stock.Wood = 0;
        Stock.Food = 0;
        Stock.Stone = 0;
    }
}
