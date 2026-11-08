using Godot;
using Edict.Core;

namespace Edict;

/// <summary>
/// 点击市民后弹出的信息面板：头像 + 姓名 + 状态。
/// 头像是程序画的写实风格占位（额光/颧影/眼窝/鼻侧/唇下），
/// 等 AI 出图后替换成 256×256 贴图，面板结构不变。
/// </summary>
public partial class InspectorPanel : CanvasLayer
{
    public CitizenSystem? Citizens { get; set; }
    public CitizenRenderer? Renderer { get; set; }

    private PanelContainer _panel = null!;
    private AvatarView _avatar = null!;
    private Label _name = null!;
    private Label _stats = null!;
    private Label _state = null!;
    private Label _hint = null!;

    private static readonly string[] Surnames =
    {
        "李", "王", "张", "赵", "陈", "杨", "刘", "黄", "周", "吴", "徐", "孙"
    };

    private static readonly string[] GivenNames =
    {
        "牧", "衡", "衍", "瑾", "砚", "舟", "岑", "珏", "珩", "琛", "翊", "晏",
        "裴", "禹", "霈", "箴", "筠", "翊", "瑄", "彦"
    };

    public override void _Ready()
    {
        _panel = new PanelContainer
        {
            Position = new Vector2(12, 400),
            Visible = false,
            CustomMinimumSize = new Vector2(320, 0),
        };
        var style = new StyleBoxFlat { BgColor = new Color(0.09f, 0.086f, 0.106f, 0.95f) };
        style.SetContentMarginAll(10);
        style.SetCornerRadiusAll(6);
        style.BorderColor = new Color("7A6229");
        style.SetBorderWidthAll(1);
        _panel.AddThemeStyleboxOverride("panel", style);
        AddChild(_panel);

        var box = new VBoxContainer();
        box.AddThemeConstantOverride("separation", 8);
        _panel.AddChild(box);

        _avatar = new AvatarView { CustomMinimumSize = new Vector2(160, 160) };
        box.AddChild(_avatar);

        _name = new Label();
        _name.AddThemeFontSizeOverride("font_size", 20);
        box.AddChild(_name);

        _state = new Label();
        _state.AddThemeFontSizeOverride("font_size", 14);
        box.AddChild(_state);

        _stats = new Label();
        _stats.AddThemeFontSizeOverride("font_size", 13);
        box.AddChild(_stats);

        _hint = new Label { Text = "ESC 取消选择" };
        _hint.AddThemeFontSizeOverride("font_size", 11);
        _hint.Modulate = new Color(1, 1, 1, 0.45f);
        box.AddChild(_hint);
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event is not InputEventMouseButton mb) return;
        if (!mb.Pressed) return;

        if (mb.ButtonIndex == MouseButton.Right)
        {
            Deselect();
            return;
        }

        if (mb.ButtonIndex != MouseButton.Left) return;
        if (Citizens == null) return;

        Vector2 world = GetViewport().GetCamera2D()?.GetGlobalMousePosition() ?? Vector2.Zero;
        int idx = Citizens.FindNearest(world.X, world.Y, 28f);

        if (idx >= 0) Select(idx);
        else Deselect();
    }

    public override void _Process(double delta)
    {
        if (!_panel.Visible || Citizens == null) return;
        if (Renderer == null) return;

        int i = Renderer.SelectedIndex;
        if (i < 0 || i >= Citizens.Count)
        {
            Deselect();
            return;
        }

        ref Citizen c = ref Citizens.At(i);
        _name.Text = NameOf(c.NameIndex);
        _state.Text = StateText(in c);
        _stats.Text =
            $"{Locale.Tr("UI_HUNGER")}: {c.Hunger:0}\n" +
            $"{Locale.Tr("UI_ENERGY")}: {c.Energy:0}\n" +
            $"{Locale.Tr("UI_MOOD")}: {c.Mood:0}\n" +
            $"{Locale.Tr("UI_POS")}: ({c.X / 48:0}, {c.Y / 48:0})";
    }

    public void SelectFirst()
    {
        if (Citizens == null || Citizens.Count == 0) return;
        Select(0);
        // 把镜头移到被选中的人身上
        var cam = GetViewport().GetCamera2D();
        if (cam != null)
        {
            ref Citizen c = ref Citizens.At(0);
            cam.Position = new Vector2(c.X, c.Y);
        }
    }

    private void Select(int index)
    {
        Renderer!.SelectedIndex = index;
        _panel.Visible = true;
        ref Citizen c = ref Citizens!.At(index);
        _avatar.Seed = c.NameIndex;
        _avatar.Profession = c.Profession;
        _avatar.QueueRedraw();
    }

    private void Deselect()
    {
        if (Renderer != null) Renderer.SelectedIndex = -1;
        _panel.Visible = false;
    }

    private static string NameOf(int index)
    {
        string s = Surnames[index % Surnames.Length];
        string g = GivenNames[(index / Surnames.Length) % GivenNames.Length];
        return s + g;
    }

    private string StateText(in Citizen c)
    {
        string prof = Locale.Tr("PROF_" + c.Profession.ToString().ToUpperInvariant());
        string act = c.State switch
        {
            CitizenState.Moving => Locale.Tr("ACT_MOVING"),
            CitizenState.Working => Locale.Tr("ACT_WORKING"),
            CitizenState.Eating => Locale.Tr("ACT_EATING"),
            _ => Locale.Tr("ACT_IDLE"),
        };
        return $"{prof} · {act}";
    }
}

/// <summary>程序画的头像占位。AI 出图后整体替换成 TextureRect。</summary>
public partial class AvatarView : Control
{
    public int Seed { get; set; }
    public Profession Profession { get; set; }

    private static readonly Color Bg0 = new("17161B");
    private static readonly Color Bg1 = new("1B1A23");
    private static readonly Color SkinBase = new("8E6B4E");
    private static readonly Color SkinLight = new("9C8263");
    private static readonly Color SkinShadow = new("574634");
    private static readonly Color HairDark = new("121119");
    private static readonly Color EyeWhite = new("C2BAA9");
    private static readonly Color Gold = new("7A6229");

    public override void _Draw()
    {
        Vector2 size = Size;
        if (size.X < 8 || size.Y < 8) return;

        float s = Mathf.Min(size.X, size.Y);
        Vector2 o = (size - new Vector2(s, s)) * 0.5f;

        DrawRect(new Rect2(o, new Vector2(s, s)), Bg0);
        for (float y = 0; y < s; y += 8f)
            DrawRect(new Rect2(o + new Vector2(0, y), new Vector2(s, 3)), Bg1);

        var rng = new System.Random(Seed);

        // 肩
        DrawCircle(o + new Vector2(s * 0.5f, s * 1.02f), s * 0.36f, new Color("3E2C46"));

        // 脖子
        DrawRect(new Rect2(o + new Vector2(s * 0.43f, s * 0.55f), new Vector2(s * 0.14f, s * 0.2f)), SkinBase);

        // 脸
        Vector2 faceC = o + new Vector2(s * 0.5f, s * 0.42f);
        DrawCircle(faceC, s * 0.23f, SkinBase);
        DrawCircle(faceC + new Vector2(-s * 0.04f, -s * 0.05f), s * 0.19f, SkinLight);

        // 头发
        DrawArc(faceC, s * 0.23f, Mathf.DegToRad(180), Mathf.DegToRad(360), 24, HairDark, s * 0.09f, true);

        // 眼窝
        float eyeY = faceC.Y + s * 0.02f;
        DrawCircle(new Vector2(faceC.X - s * 0.09f, eyeY), s * 0.045f, SkinShadow);
        DrawCircle(new Vector2(faceC.X + s * 0.09f, eyeY), s * 0.045f, SkinShadow);

        // 眼
        DrawCircle(new Vector2(faceC.X - s * 0.09f, eyeY), s * 0.032f, EyeWhite);
        DrawCircle(new Vector2(faceC.X + s * 0.09f, eyeY), s * 0.032f, EyeWhite);
        DrawCircle(new Vector2(faceC.X - s * 0.09f, eyeY), s * 0.016f, HairDark);
        DrawCircle(new Vector2(faceC.X + s * 0.09f, eyeY), s * 0.016f, HairDark);

        // 眉
        float browTilt = (float)(rng.NextDouble() - 0.5) * 0.02f;
        DrawLine(new Vector2(faceC.X - s * 0.14f, faceC.Y - s * 0.05f + browTilt * s),
                 new Vector2(faceC.X - s * 0.04f, faceC.Y - s * 0.07f - browTilt * s), HairDark, s * 0.018f);
        DrawLine(new Vector2(faceC.X + s * 0.04f, faceC.Y - s * 0.07f - browTilt * s),
                 new Vector2(faceC.X + s * 0.14f, faceC.Y - s * 0.05f + browTilt * s), HairDark, s * 0.018f);

        // 鼻
        DrawLine(new Vector2(faceC.X, faceC.Y + s * 0.03f),
                 new Vector2(faceC.X, faceC.Y + s * 0.09f), SkinShadow, s * 0.014f);

        // 嘴
        DrawLine(new Vector2(faceC.X - s * 0.05f, faceC.Y + s * 0.13f),
                 new Vector2(faceC.X + s * 0.05f, faceC.Y + s * 0.13f), SkinShadow, s * 0.016f);

        // 金边
        DrawRect(new Rect2(o, new Vector2(s, s)), Gold, false, 1.5f);
    }
}
