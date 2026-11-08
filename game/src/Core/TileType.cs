namespace Edict.Core;

/// <summary>地形类型。数值写入存档，不可随意重排。</summary>
public enum TileType : byte
{
    Void = 0,
    Water = 1,
    Sand = 2,
    Grass = 3,
    Forest = 4,
    Rock = 5,
}
