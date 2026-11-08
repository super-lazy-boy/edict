using Godot;
using Edict.Core;

namespace Edict;

/// <summary>
/// 建造工具：底部选建筑，鼠标移到地图上显示预览，左键放置。
/// </summary>
public partial class BuildTool : CanvasLayer
{
    public BuildingSystem? Buildings { get; set; }
    public BuildingRenderer? Renderer { get; set; }
    public CitizenSystem? Citizens { get; set; }

    /// <summary>是否处于放置模式——为真时其他系统不应响应左键。</summary>
    public static bool IsActive { get; private set; }

    public BuildingType Pending { get; private set; } = BuildingType.None;

    private readonly System.Collections.Generic.List<Button> _buttons = new();
    private Label _hint = null!;

    private static readonly BuildingType[] Palette =
    {
        BuildingType.House,
        BuildingType.Farm,
        BuildingType.Warehouse,
        BuildingType.LumberCamp,
    };

    public override void _Ready()
    {
        var bar = new HBoxContainer
        {
            Position = new Vector2(12, 0),
            CustomMinimumSize = new Vector2(0, 40),
        };
        AddChild(bar);

        // 锚到底部
        bar.SetAnchorsPreset(Control.LayoutPreset.BottomWide);
        bar.OffsetLeft = 12;
        bar.OffsetTop = -56;
        bar.OffsetBottom = -12;
        bar.OffsetRight = -12;

        var panel = new PanelContainer();
        var style = new StyleBoxFlat { BgColor = new Color(0.09f, 0.086f, 0.106f, 0.92f) };
        style.SetContentMarginAll(6);
        style.SetCornerRadiusAll(6);
        style.BorderColor = new Color("26242E");
        style.SetBorderWidthAll(1);
        panel.AddThemeStyleboxOverride("panel", style);
        AddChild(panel);
        panel.SetAnchorsPreset(Control.LayoutPreset.BottomWide);
        panel.OffsetLeft = 12;
        panel.OffsetTop = -60;
        panel.OffsetBottom = -12;
        panel.OffsetRight = -12;

        var row = new HBoxContainer();
        row.AddThemeConstantOverride("separation", 8);
        panel.AddChild(row);

        foreach (var t in Palette)
        {
            var def = BuildingDef.Get(t);
            var b = new Button
            {
                Text = Locale.Tr(def.NameKey),
                CustomMinimumSize = new Vector2(120, 34),
            };
            var captured = t;
            b.Pressed += () => Toggle(captured);
            row.AddChild(b);
            _buttons.Add(b);
        }

        _hint = new Label { Text = "" };
        _hint.AddThemeFontSizeOverride("font_size", 13);
        row.AddChild(_hint);

        RebuildTexts();
    }

    public void RebuildTexts()
    {
        for (int i = 0; i < Palette.Length; i++)
        {
            var def = BuildingDef.Get(Palette[i]);
            _buttons[i].Text = Locale.Tr(def.NameKey);
        }
        _hint.Text = IsActive ? Locale.Tr("BUILD_HINT_ACTIVE") : Locale.Tr("BUILD_HINT_IDLE");
    }

    private void Toggle(BuildingType t)
    {
        if (Pending == t)
        {
            Cancel();
            return;
        }

        Pending = t;
        IsActive = true;
        if (Renderer != null) Renderer.GhostType = t;
        RebuildTexts();
    }

    public void Cancel()
    {
        Pending = BuildingType.None;
        IsActive = false;
        if (Renderer != null) Renderer.GhostType = BuildingType.None;
        RebuildTexts();
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event is InputEventKey k && k.Pressed && !k.Echo && k.Keycode == Key.Escape)
        {
            if (IsActive) Cancel();
            return;
        }

        if (@event is not InputEventMouseButton mb) return;
        if (mb.ButtonIndex == MouseButton.Right && mb.Pressed)
        {
            Cancel();
            return;
        }
        if (!mb.Pressed || mb.ButtonIndex != MouseButton.Left) return;
        if (!IsActive || Buildings == null) return;

        Vector2 world = GetViewport().GetCamera2D()?.GetGlobalMousePosition() ?? Vector2.Zero;
        int tx = (int)(world.X / BuildingSystem.TileSize);
        int ty = (int)(world.Y / BuildingSystem.TileSize);

        var def = BuildingDef.Get(Pending);
        if (!Buildings.CanPlace(tx, ty, Pending))
        {
            GD.Print($"[Build] 无法在此放置 {Pending} @ ({tx},{ty})");
            return;
        }

        if (!Buildings.Stock.TrySpendWood(def.WoodCost))
        {
            GD.Print($"[Build] 木材不足：需要 {def.WoodCost}，现有 {Buildings.Stock.Wood:0}");
            return;
        }

        Buildings.Place(tx, ty, Pending);
        GD.Print($"[Build] 已下单 {Pending} @ ({tx},{ty})");

        // 放完继续保持模式，方便连点
    }

    public override void _Process(double delta)
    {
        if (!IsActive || Renderer == null) return;

        Vector2 world = GetViewport().GetCamera2D()?.GetGlobalMousePosition() ?? Vector2.Zero;
        Renderer.GhostTileX = (int)(world.X / BuildingSystem.TileSize);
        Renderer.GhostTileY = (int)(world.Y / BuildingSystem.TileSize);
    }
}
