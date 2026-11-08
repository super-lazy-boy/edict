using System;

namespace Edict.Core;

/// <summary>
/// 存档数据。版本号用于迁移，不可删除旧版本处理分支。
/// </summary>
public sealed class SaveData
{
    public const int CurrentVersion = 1;

    public int Version { get; set; } = CurrentVersion;
    public int Width { get; set; }
    public int Height { get; set; }
    public int Seed { get; set; }
    public TileType[] Tiles { get; set; } = Array.Empty<TileType>();
    public long Tick { get; set; }
    public string Language { get; set; } = "zh_CN";
    public long SavedAtUnix { get; set; }
}
