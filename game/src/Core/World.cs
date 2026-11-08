using System;

namespace Edict.Core;

/// <summary>
/// 世界地图数据。纯逻辑，不依赖引擎。
/// 地图像素/瓦片只存类型，渲染由引擎层决定。
/// </summary>
public sealed class World
{
    public int Width { get; }
    public int Height { get; }
    public int Seed { get; }

    private readonly TileType[] _tiles;

    /// <summary>被渡口覆盖的水域：可安全通行、代价低。</summary>
    private readonly bool[] _ferryWater;

    public World(int width, int height, int seed)
    {
        if (width <= 0 || height <= 0) throw new ArgumentOutOfRangeException(nameof(width));
        Width = width;
        Height = height;
        Seed = seed;
        _tiles = new TileType[width * height];
        _ferryWater = new bool[width * height];
        Generate();
    }

    private World(int width, int height, int seed, TileType[] tiles)
    {
        Width = width;
        Height = height;
        Seed = seed;
        _tiles = tiles;
        _ferryWater = new bool[width * height];
    }

    public TileType this[int x, int y]
    {
        get
        {
            if (x < 0 || y < 0 || x >= Width || y >= Height) return TileType.Void;
            return _tiles[y * Width + x];
        }
    }

    public bool InBounds(int x, int y) => x >= 0 && y >= 0 && x < Width && y < Height;

    /// <summary>改写单个瓦片。市民砍树会把森林变成草地。</summary>
    public void SetTile(int x, int y, TileType type)
    {
        if (!InBounds(x, y)) return;
        _tiles[y * Width + x] = type;
        if (type != TileType.Water) _ferryWater[y * Width + x] = false;
    }

    /// <summary>该水域是否被渡口覆盖（可安全通过）。</summary>
    public bool IsFerryWater(int x, int y)
        => InBounds(x, y) && _ferryWater[y * Width + x];

    /// <summary>渡口建成时，把周围水域标记为安全航道。</summary>
    public void MarkFerryWater(int cx, int cy, int radius)
    {
        for (int dy = -radius; dy <= radius; dy++)
        {
            for (int dx = -radius; dx <= radius; dx++)
            {
                if (dx * dx + dy * dy > radius * radius) continue;
                int x = cx + dx, y = cy + dy;
                if (!InBounds(x, y)) continue;
                if (_tiles[y * Width + x] != TileType.Water) continue;
                _ferryWater[y * Width + x] = true;
            }
        }
    }

    /// <summary>某个水格附近（半径 r）是否有陆地，用于判断能否建渡口。</summary>
    public bool HasLandNear(int cx, int cy, int radius)
    {
        for (int dy = -radius; dy <= radius; dy++)
        {
            for (int dx = -radius; dx <= radius; dx++)
            {
                int x = cx + dx, y = cy + dy;
                if (!InBounds(x, y)) continue;
                var t = _tiles[y * Width + x];
                if (t != TileType.Water && t != TileType.Void && t != TileType.Rock)
                    return true;
            }
        }
        return false;
    }

    public TileType[] Tiles => _tiles;

    // ---------- 生成 ----------

    private void Generate()
    {
        for (int y = 0; y < Height; y++)
        {
            for (int x = 0; x < Width; x++)
            {
                float nx = x / (float)Width;
                float ny = y / (float)Height;

                float elevation = Fbm(nx * 4f, ny * 4f, 4);
                float moisture = Fbm(nx * 3f + 17.3f, ny * 3f + 5.1f, 3);

                TileType t;
                if (elevation < 0.36f) t = TileType.Water;
                else if (elevation < 0.41f) t = TileType.Sand;
                else if (elevation > 0.78f) t = TileType.Rock;
                else if (moisture > 0.55f) t = TileType.Forest;
                else t = TileType.Grass;

                _tiles[y * Width + x] = t;
            }
        }
    }

    private float Fbm(float x, float y, int octaves)
    {
        float sum = 0f, amp = 0.5f, freq = 1f, norm = 0f;
        for (int i = 0; i < octaves; i++)
        {
            sum += ValueNoise(x * freq, y * freq) * amp;
            norm += amp;
            amp *= 0.5f;
            freq *= 2f;
        }
        return sum / norm;
    }

    private float ValueNoise(float x, float y)
    {
        int x0 = (int)MathF.Floor(x);
        int y0 = (int)MathF.Floor(y);
        float fx = Smooth(x - x0);
        float fy = Smooth(y - y0);

        float v00 = Hash(x0, y0);
        float v10 = Hash(x0 + 1, y0);
        float v01 = Hash(x0, y0 + 1);
        float v11 = Hash(x0 + 1, y0 + 1);

        float a = Lerp(v00, v10, fx);
        float b = Lerp(v01, v11, fx);
        return Lerp(a, b, fy);
    }

    private float Hash(int x, int y)
    {
        unchecked
        {
            uint h = (uint)(x * 374761393 + y * 668265263 + Seed * 1274126177);
            h = (h ^ (h >> 13)) * 1274126177u;
            h ^= h >> 16;
            return (h & 0xFFFFFF) / (float)0xFFFFFF;
        }
    }

    private static float Smooth(float t) => t * t * (3f - 2f * t);
    private static float Lerp(float a, float b, float t) => a + (b - a) * t;

    // ---------- 存档 ----------

    public SaveData ToSave() => new()
    {
        Width = Width,
        Height = Height,
        Seed = Seed,
        Tiles = (TileType[])_tiles.Clone(),
    };

    public static World FromSave(SaveData data)
    {
        if (data.Tiles.Length != data.Width * data.Height)
            throw new InvalidOperationException("存档瓦片数量与尺寸不符");
        return new World(data.Width, data.Height, data.Seed, data.Tiles);
    }
}
