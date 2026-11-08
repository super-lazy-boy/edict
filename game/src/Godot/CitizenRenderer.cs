using Godot;
using Edict.Core;

namespace Edict;

/// <summary>
/// 市民渲染。启动时把每个职业预渲染成 32×32 贴图，运行时每人只发一次绘制调用。
/// 这是撑住 2000 人的关键——不要用 DrawCircle 逐人画。
/// </summary>
public partial class CitizenRenderer : Node2D
{
    public CitizenSystem? Citizens { get; set; }
    public int SelectedIndex { get; set; } = -1;

    private const int Sprite = 32;
    private const int Half = Sprite / 2;

    private readonly ImageTexture?[] _textures = new ImageTexture?[6];

    // 职业服装色：必须和草地（green3 #435433）拉开对比
    private static readonly Color[] Cloth =
    {
        new("836B50"), // 农民 sand1
        new("765A3F"), // 工匠 wood4
        new("324E5C"), // 商人 blue3
        new("948E99"), // 士兵 gray4
        new("3E2C46"), // 官员 purple
        new("7A6229"), // 贵族 gold0
    };

    private static readonly Color HairNormal = new("121119");
    private static readonly Color HairNoble = new("A2853A");
    private static readonly Color Skin = new("8E6B4E");
    private static readonly Color Ink = new("0A090C");
    private static readonly Color Select = new("E2DACA");

    public int LastDrawn { get; private set; }

    public override void _Ready()
    {
        for (int i = 0; i < 6; i++)
        {
            var hair = i == (int)Profession.Noble ? HairNoble : HairNormal;
            _textures[i] = BuildSprite(Cloth[i], hair);
        }
    }

    public override void _Process(double delta) => QueueRedraw();

    public override void _Draw()
    {
        if (Citizens == null) return;

        var cam = GetViewport().GetCamera2D();
        if (cam == null) return;

        Vector2 center = cam.GetScreenCenterPosition();
        Vector2 half = GetViewportRect().Size * 0.5f / cam.Zoom;
        Rect2 view = new(center - half, half * 2f);
        view = view.Grow(Half + 4);

        var span = Citizens.Citizens;
        int drawn = 0;

        for (int i = 0; i < span.Length; i++)
        {
            ref readonly Citizen c = ref span[i];
            if (c.Alive == 0) continue;

            var pos = new Vector2(c.X, c.Y);
            if (!view.HasPoint(pos)) continue;

            var tex = _textures[(int)c.Profession];
            if (tex != null)
                DrawTexture(tex, new Vector2(c.X - Half, c.Y - Half));

            drawn++;
        }

        // 选中环只画一个，单独处理
        if (SelectedIndex >= 0 && SelectedIndex < span.Length)
        {
            ref readonly Citizen sc = ref span[SelectedIndex];
            DrawArc(new Vector2(sc.X, sc.Y), 15f, 0, Mathf.Tau, 24, Select, 1.8f, true);
        }

        LastDrawn = drawn;
    }

    // ---------------- 贴图生成 ----------------

    private static ImageTexture BuildSprite(Color cloth, Color hair)
    {
        var img = Image.CreateEmpty(Sprite, Sprite, false, Image.Format.Rgba8);
        img.Fill(new Color(0, 0, 0, 0));

        float cx = Half, cy = Half;

        // 投影（右下偏移）
        Disc(img, cx + 2, cy + 3, 9.5f, new Color(0, 0, 0, 0.32f));

        // 身体外描边
        Disc(img, cx, cy, 9.8f, Ink);
        // 身体
        Disc(img, cx, cy, 9f, cloth);
        Disc(img, cx - 1, cy - 1, 7f, cloth.Lightened(0.10f));

        // 头顶外描边
        Disc(img, cx, cy - 2, 7.3f, Ink);
        // 头顶
        Disc(img, cx, cy - 2, 6.5f, hair);
        Disc(img, cx - 1, cy - 3, 5f, hair.Lightened(0.12f));

        // 鼻尖：提示朝向
        Disc(img, cx, cy + 6, 2.2f, Skin);

        return ImageTexture.CreateFromImage(img);
    }

    /// <summary>在 Image 上画实心圆（无抗锯齿，符合像素风）。</summary>
    private static void Disc(Image img, float cx, float cy, float r, Color col)
    {
        int x0 = Mathf.FloorToInt(cx - r), x1 = Mathf.CeilToInt(cx + r);
        int y0 = Mathf.FloorToInt(cy - r), y1 = Mathf.CeilToInt(cy + r);
        int w = img.GetWidth(), h = img.GetHeight();

        for (int y = y0; y <= y1; y++)
        {
            if (y < 0 || y >= h) continue;
            for (int x = x0; x <= x1; x++)
            {
                if (x < 0 || x >= w) continue;
                float dx = x + 0.5f - cx;
                float dy = y + 0.5f - cy;
                if (dx * dx + dy * dy <= r * r)
                    img.SetPixel(x, y, col);
            }
        }
    }
}
