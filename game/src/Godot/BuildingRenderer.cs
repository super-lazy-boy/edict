using Godot;
using Edict.Core;

namespace Edict;

/// <summary>
/// 建筑渲染。投影 C：屋面 60% + 檐口阴影 + 南墙 30%。
/// 未完工的建筑画脚手架和进度条。
/// </summary>
public partial class BuildingRenderer : Node2D
{
    public BuildingSystem? Buildings { get; set; }

    /// <summary>放置预览：建筑类型 + 瓦片坐标；None 表示不在放置模式。</summary>
    public BuildingType GhostType { get; set; } = BuildingType.None;
    public int GhostTileX { get; set; }
    public int GhostTileY { get; set; }

    private static readonly Color ShadowC = new(0f, 0f, 0f, 0.35f);
    private static readonly Color RoofLit = new("6B3125");   // red2
    private static readonly Color RoofShade = new("54241C"); // red1
    private static readonly Color Ridge = new("4C3826");     // wood2
    private static readonly Color Wall = new("C2BAA9");      // bone0
    private static readonly Color WallShade = new("9C8263"); // sand2
    private static readonly Color Door = new("3A2A1D");      // wood1
    private static readonly Color Outline = new("0A090C");   // ink0
    private static readonly Color Scaffold = new("765A3F");  // wood4
    private static readonly Color Ok = new(0.6f, 0.9f, 0.6f, 0.35f);
    private static readonly Color Bad = new(0.9f, 0.3f, 0.3f, 0.35f);

    public override void _Process(double delta) => QueueRedraw();

    public override void _Draw()
    {
        if (Buildings == null) return;

        var list = Buildings.Buildings;
        for (int i = 0; i < list.Count; i++)
        {
            var b = list[i];
            DrawBuilding(in b);
        }

        DrawGhost();
    }

    private void DrawBuilding(in Building b)
    {
        var def = BuildingDef.Get(b.Type);
        float ts = BuildingSystem.TileSize;
        float x = b.TileX * ts;
        float y = b.TileY * ts;
        float w = def.Size * ts;

        if (b.Type == BuildingType.Ferry)
        {
            DrawFerry(x, y, w, b.Complete);
            return;
        }

        if (!b.Complete)
        {
            // 地基 + 脚手架
            DrawRect(new Rect2(x + 4, y + 4, w - 8, w - 8), Scaffold, false, 2f);
            for (float gx = x + 4; gx < x + w - 4; gx += 12)
                DrawLine(new Vector2(gx, y + 4), new Vector2(gx, y + w - 4), Scaffold, 1f);
            for (float gy = y + 4; gy < y + w - 4; gy += 12)
                DrawLine(new Vector2(x + 4, gy), new Vector2(x + w - 4, gy), Scaffold, 1f);
            return;
        }

        // 投影
        DrawRect(new Rect2(x + 6, y + 7, w - 8, w - 8), ShadowC);

        // 屋面（上坡受光 / 下坡背光）
        float roofH = w * 0.62f;
        float ridgeY = y + roofH * 0.55f;

        DrawRect(new Rect2(x + 2, y + 2, w - 4, ridgeY - y), RoofLit);
        DrawRect(new Rect2(x + 2, ridgeY, w - 4, y + roofH - ridgeY), RoofShade);

        // 瓦缝：横向短线
        for (float ly = y + 6; ly < y + roofH; ly += 8)
            DrawLine(new Vector2(x + 3, ly), new Vector2(x + w - 3, ly),
                     ly < ridgeY ? RoofShade : Outline, 1f);

        // 屋脊
        DrawRect(new Rect2(x, ridgeY - 2, w, 4), Ridge);
        DrawLine(new Vector2(x, ridgeY - 2), new Vector2(x + w, ridgeY - 2), new Color("765A3F"), 1f);

        // 檐口阴影
        DrawRect(new Rect2(x + 2, y + roofH, w - 4, 4), Outline);

        // 南墙
        float wallTop = y + roofH + 4;
        DrawRect(new Rect2(x + 4, wallTop, w - 8, y + w - wallTop - 2), Wall);
        DrawRect(new Rect2(x + 4, wallTop, w - 8, 3), WallShade);

        // 门
        float dw = w * 0.16f;
        DrawRect(new Rect2(x + w * 0.5f - dw * 0.5f, wallTop + 6, dw, y + w - wallTop - 8), Door);

        // 外框
        DrawRect(new Rect2(x + 2, y + 2, w - 4, w - 4), Outline, false, 1.5f);
    }

    /// <summary>渡口：木栈桥 + 小舟。</summary>
    private void DrawFerry(float x, float y, float w, bool complete)
    {
        var plank = new Color("5F4831");
        var plankDark = new Color("3A2A1D");
        var post = new Color("2A1E15");

        if (!complete)
        {
            DrawRect(new Rect2(x + 6, y + 6, w - 12, w - 12), Scaffold, false, 2f);
            return;
        }

        // 栈桥
        DrawRect(new Rect2(x + 4, y + 10, w - 8, w - 20), plank);
        for (float py = y + 12; py < y + w - 10; py += 6)
            DrawLine(new Vector2(x + 4, py), new Vector2(x + w - 4, py), plankDark, 1f);

        // 桥桩
        DrawRect(new Rect2(x + 4, y + 10, 3, w - 20), post);
        DrawRect(new Rect2(x + w - 7, y + 10, 3, w - 20), post);

        // 小舟
        DrawRect(new Rect2(x + w * 0.32f, y + w * 0.36f, w * 0.36f, w * 0.26f), plank);
        DrawLine(new Vector2(x + w * 0.32f, y + w * 0.62f), new Vector2(x + w * 0.68f, y + w * 0.62f), post, 2f);

        DrawRect(new Rect2(x + 4, y + 10, w - 8, w - 20), Outline, false, 1.5f);
    }

    private void DrawGhost()
    {
        if (GhostType == BuildingType.None || Buildings == null) return;

        var def = BuildingDef.Get(GhostType);
        float ts = BuildingSystem.TileSize;
        float x = GhostTileX * ts;
        float y = GhostTileY * ts;
        float w = def.Size * ts;

        bool ok = Buildings.CanPlace(GhostTileX, GhostTileY, GhostType);
        DrawRect(new Rect2(x, y, w, w), ok ? Ok : Bad);
        DrawRect(new Rect2(x, y, w, w), ok ? new Color(0.7f, 1f, 0.7f) : new Color(1f, 0.5f, 0.5f), false, 2f);
    }
}
