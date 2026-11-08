using Godot;

namespace Edict;

/// <summary>
/// 调试用 HUD。M0 阶段显示性能与状态，正式 UI 后替换。
/// </summary>
public partial class Hud : CanvasLayer
{
    public Main Main { get; set; } = null!;

    private Label _stats = null!;
    private Label _toast = null!;
    private Button _langBtn = null!;
    private Button _saveBtn = null!;
    private Button _loadBtn = null!;
    private Button _newBtn = null!;
    private Button _speedBtn = null!;

    private double _toastTimer;

    public override void _Ready() => Build();

    private void Build()
    {
        var panel = new PanelContainer
        {
            Position = new Vector2(12, 12),
            CustomMinimumSize = new Vector2(340, 0),
        };
        var style = new StyleBoxFlat { BgColor = new Color(0f, 0f, 0f, 0.7f) };
        style.SetContentMarginAll(10);
        style.SetCornerRadiusAll(6);
        panel.AddThemeStyleboxOverride("panel", style);
        AddChild(panel);

        var vbox = new VBoxContainer();
        vbox.AddThemeConstantOverride("separation", 8);
        panel.AddChild(vbox);

        var title = new Label { Text = "EDICT / 敕令" };
        title.AddThemeFontSizeOverride("font_size", 18);
        vbox.AddChild(title);

        _stats = new Label();
        _stats.AddThemeFontSizeOverride("font_size", 13);
        vbox.AddChild(_stats);

        var row1 = new HBoxContainer();
        vbox.AddChild(row1);

        _langBtn = MakeButton(row1);
        _langBtn.Pressed += () => { Locale.Toggle(); RebuildTexts(); };

        _saveBtn = MakeButton(row1);
        _saveBtn.Pressed += () => { bool ok = Main.SaveGame(); Toast(ok ? "MSG_SAVED" : "MSG_SAVE_FAIL"); };

        _loadBtn = MakeButton(row1);
        _loadBtn.Pressed += () => { bool ok = Main.LoadGame(); Toast(ok ? "MSG_LOADED" : "MSG_LOAD_FAIL"); };

        var row2 = new HBoxContainer();
        vbox.AddChild(row2);

        _newBtn = MakeButton(row2);
        _newBtn.Pressed += () =>
        {
            Main.NewWorld((int)(Time.GetTicksMsec() & 0x7FFFFFFF));
            Toast("MSG_LOADED");
        };

        _speedBtn = MakeButton(row2);
        _speedBtn.Pressed += () => CycleSpeed();

        _toast = new Label
        {
            Position = new Vector2(12, 0),
            Modulate = new Color(1, 1, 1, 0f),
        };
        _toast.AddThemeFontSizeOverride("font_size", 16);
        AddChild(_toast);

        RebuildTexts();
    }

    private static Button MakeButton(Container parent)
    {
        var b = new Button { CustomMinimumSize = new Vector2(0, 28) };
        parent.AddChild(b);
        return b;
    }

    public void RebuildTexts()
    {
        _langBtn.Text = Locale.Tr("UI_LANG_TOGGLE");
        _saveBtn.Text = Locale.Tr("UI_SAVE");
        _loadBtn.Text = Locale.Tr("UI_LOAD");
        _newBtn.Text = Locale.Tr("UI_NEW");
        _speedBtn.Text = $"{Locale.Tr("UI_SPEED")} {Main.Clock.Speed:0.#}x";
    }

    private void CycleSpeed()
    {
        double s = Main.Clock.Speed;
        double next = s switch
        {
            < 1.0 => 1.0,
            < 2.0 => 2.0,
            < 3.0 => 3.0,
            < 10.0 => 10.0,
            _ => 0.0,
        };
        Main.Clock.Speed = next;
        _speedBtn.Text = next == 0.0
            ? Locale.Tr("UI_PAUSE")
            : $"{Locale.Tr("UI_SPEED")} {next:0.#}x";
    }

    public void Refresh()
    {
        if (_stats == null || Main?.World == null) return;

        var cam = GetViewport().GetCamera2D();
        string camText = cam == null ? "-" : $"({cam.Position.X:0}, {cam.Position.Y:0}) x{cam.Zoom.X:0.00}";

        _stats.Text =
            $"{Locale.Tr("HUD_FPS")}: {Engine.GetFramesPerSecond():0}\n" +
            $"{Locale.Tr("HUD_TICK")}: {Main.Clock.Tick}\n" +
            $"{Locale.Tr("HUD_SPEED")}: {Main.Clock.Speed:0.#}x\n" +
            $"{Locale.Tr("HUD_POP")}: {Main.Citizens?.Count ?? 0}\n" +
            $"{Locale.Tr("HUD_JOBS")}: {Main.Citizens?.Jobs.PendingCount ?? 0}\n" +
            $"{Locale.Tr("HUD_CAM")}: {camText}\n" +
            $"{Locale.Tr("HUD_DRAWN")}: {Main.Renderer?.LastDrawnTiles ?? 0}\n" +
            $"{Locale.Tr("HUD_SEED")}: {Main.World.Seed}\n" +
            $"{Locale.Tr("HELP_PAN")} · {Locale.Tr("HELP_ZOOM")}\n" +
            $"{Locale.Tr("HELP_SELECT")}";

        if (_toastTimer > 0)
        {
            _toastTimer -= GetProcessDeltaTime();
            _toast.Modulate = new Color(1, 1, 1, (float)Mathf.Clamp(_toastTimer, 0, 1));
        }
    }

    private void Toast(string key)
    {
        _toast.Text = Locale.Tr(key);
        _toast.Position = new Vector2(12, 12 + 260);
        _toastTimer = 2.0;
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event is not InputEventKey k || !k.Pressed || k.Echo) return;

        switch (k.Keycode)
        {
            case Key.F5: Main.SaveGame(); Toast("MSG_SAVED"); break;
            case Key.F9: Main.LoadGame(); Toast("MSG_LOADED"); break;
            case Key.Space: CycleSpeed(); break;
        }
    }
}
