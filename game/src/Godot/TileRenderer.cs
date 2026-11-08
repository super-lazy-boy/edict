using Godot;
using Edict.Core;

namespace Edict;

/// <summary>
/// 瓦片渲染。只绘制视口范围内的瓦片（视锥裁剪）。
/// 美术接入后，把 DrawRect 换成 DrawTextureRect 即可，裁剪逻辑不变。
/// </summary>
public partial class TileRenderer : Node2D
{
    public const int TileSize = 32;

    public World World { get; set; } = null!;

    private static readonly Color[] Palette =
    {
        new(0.05f, 0.05f, 0.07f),   // Void
        new(0.16f, 0.35f, 0.52f),   // Water
        new(0.72f, 0.66f, 0.48f),   // Sand
        new(0.38f, 0.55f, 0.30f),   // Grass
        new(0.20f, 0.36f, 0.20f),   // Forest
        new(0.44f, 0.44f, 0.46f),   // Rock
    };

    public int LastDrawnTiles { get; private set; }

    public override void _Process(double delta) => QueueRedraw();

    public override void _Draw()
    {
        if (World == null) return;

        var cam = GetViewport().GetCamera2D();
        if (cam == null) return;

        Vector2 center = cam.GetScreenCenterPosition();
        Vector2 half = GetViewportRect().Size * 0.5f / cam.Zoom;
        Rect2 view = new(center - half, half * 2f);

        int x0 = Mathf.Max(0, Mathf.FloorToInt(view.Position.X / TileSize) - 1);
        int y0 = Mathf.Max(0, Mathf.FloorToInt(view.Position.Y / TileSize) - 1);
        int x1 = Mathf.Min(World.Width - 1, Mathf.CeilToInt(view.End.X / TileSize) + 1);
        int y1 = Mathf.Min(World.Height - 1, Mathf.CeilToInt(view.End.Y / TileSize) + 1);

        int drawn = 0;
        for (int y = y0; y <= y1; y++)
        {
            for (int x = x0; x <= x1; x++)
            {
                var t = World[x, y];
                var rect = new Rect2(x * TileSize, y * TileSize, TileSize, TileSize);
                DrawRect(rect, Palette[(int)t], true);
                drawn++;
            }
        }
        LastDrawnTiles = drawn;

        // 放大时画网格，方便对齐
        if (cam.Zoom.X >= 1.5f)
        {
            var grid = new Color(0f, 0f, 0f, 0.12f);
            for (int x = x0; x <= x1 + 1; x++)
                DrawLine(new Vector2(x * TileSize, y0 * TileSize), new Vector2(x * TileSize, (y1 + 1) * TileSize), grid);
            for (int y = y0; y <= y1 + 1; y++)
                DrawLine(new Vector2(x0 * TileSize, y * TileSize), new Vector2((x1 + 1) * TileSize, y * TileSize), grid);
        }
    }
}
