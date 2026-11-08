using Godot;
using System.Linq;
using Edict.Core;

namespace Edict;

/// <summary>
/// 引擎入口。只负责装配各层，不写游戏规则。
/// </summary>
public partial class Main : Node2D
{
    public const int MapSize = 128;
    public const int DefaultSeed = 20261108;
    public const int DefaultPopulation = 120;

    public World World { get; private set; } = null!;
    public SimClock Clock { get; private set; } = new();
    public CitizenSystem Citizens { get; private set; } = null!;
    public BuildingSystem Buildings { get; private set; } = null!;
    public CivId Civ { get; private set; } = CivId.Jixia;

    private TileRenderer _renderer = null!;
    private BuildingRenderer _buildingRenderer = null!;
    private CitizenRenderer _citizenRenderer = null!;
    private CameraController _camera = null!;
    private InspectorPanel _inspector = null!;
    private BuildTool _buildTool = null!;
    private Hud _hud = null!;

    private const string SavePath = "user://saves/slot1.json";

    public TileRenderer? Renderer => _renderer;

    private int _shotFrames = -1;
    private ulong _startTicks;
    private int _frameCount;
    private int _population = DefaultPopulation;

    public override void _Ready()
    {
        Locale.Load();

        // 命令行可指定国风：--civ=0..5
        foreach (var a in OS.GetCmdlineUserArgs())
        {
            if (a.StartsWith("--civ=") && int.TryParse(a[6..], out int cv) && cv >= 0 && cv < 6)
                Civ = (CivId)cv;
        }

        _population = OS.GetCmdlineUserArgs().Contains("--nopop") ? 0 : DefaultPopulation;
        NewWorld(DefaultSeed);

        _renderer = new TileRenderer { World = World };
        AddChild(_renderer);

        _buildingRenderer = new BuildingRenderer { Buildings = Buildings };
        AddChild(_buildingRenderer);

        _citizenRenderer = new CitizenRenderer { Citizens = Citizens };
        AddChild(_citizenRenderer);

        _camera = new CameraController { World = World };
        AddChild(_camera);

        _inspector = new InspectorPanel { Citizens = Citizens, Renderer = _citizenRenderer };
        AddChild(_inspector);

        _buildTool = new BuildTool { Buildings = Buildings, Renderer = _buildingRenderer, Citizens = Citizens };
        AddChild(_buildTool);

        _hud = new Hud { Main = this };
        AddChild(_hud);

        GD.Print($"[Edict] 启动完成 国风={Civ}");

        if (OS.GetCmdlineUserArgs().Contains("--shot"))
        {
            _shotFrames = 300;
            GD.Print("[Edict] 截图模式");
        }

        if (OS.GetCmdlineUserArgs().Contains("--fast"))
        {
            Clock.Speed = 10.0;
            _shotFrames = 400;
            GD.Print("[Edict] 加速模式 10x");
        }

        if (OS.GetCmdlineUserArgs().Contains("--select"))
        {
            _inspector.SelectFirst();
            GD.Print("[Edict] 自动选中市民 0");
        }

        // 演示：自动放几座建筑，用于验证建造与生产
        if (OS.GetCmdlineUserArgs().Contains("--demo"))
        {
            int hx = (int)(Citizens.HomeX / BuildingSystem.TileSize);
            int hy = (int)(Citizens.HomeY / BuildingSystem.TileSize);
            int ok = 0;
            ok += TryPlaceNear(BuildingType.LumberCamp, hx + 3, hy - 3) ? 1 : 0;
            ok += TryPlaceNear(BuildingType.Farm, hx - 6, hy + 1) ? 1 : 0;
            ok += TryPlaceNear(BuildingType.Warehouse, hx + 1, hy + 4) ? 1 : 0;
            ok += TryPlaceNear(BuildingType.House, hx - 4, hy - 5) ? 1 : 0;
            GD.Print($"[Edict] 演示建筑已放置 {ok}/4");
        }

        _startTicks = Time.GetTicksMsec();
    }

    public override void _Process(double delta)
    {
        _frameCount++;

        int ticks = Clock.Advance(delta);
        for (int i = 0; i < ticks; i++)
        {
            Citizens?.Tick((float)SimClock.TickSeconds);
            Buildings?.Tick((float)SimClock.TickSeconds);
        }

        _hud.Refresh();

        if (_shotFrames > 0)
        {
            _shotFrames--;
            if (_shotFrames == 0) CaptureAndQuit();
        }
    }

    private void CaptureAndQuit()
    {
        double secs = (Time.GetTicksMsec() - _startTicks) / 1000.0;
        double avgFps = _frameCount / secs;
        GD.Print($"[PERF] frames={_frameCount} secs={secs:0.00} avg_fps={avgFps:0.0} engine_fps={Engine.GetFramesPerSecond():0.0}");
        GD.Print($"[SIM] citizens={Citizens.Count} jobs_pending={Citizens.Jobs.PendingCount} jobs_done={Citizens.Jobs.DoneCount}");
        GD.Print($"[ECO] buildings={Buildings.Count} wood={Buildings.Stock.Wood:0.0} food={Buildings.Stock.Food:0.0} cap={Buildings.Stock.Capacity}");

        try
        {
            var img = GetViewport().GetTexture().GetImage();
            img.SavePng("D:/Work/edict/docs/shot.png");
            GD.Print("[Edict] 截图已保存");
        }
        catch (System.Exception e)
        {
            GD.PushError($"[Edict] 截图失败: {e.Message}");
        }
        GetTree().Quit();
    }

    public void NewWorld(int seed)
    {
        World = new World(MapSize, MapSize, seed);
        Clock = new SimClock();
        Citizens = new CitizenSystem(World, seed);
        Citizens.Spawn(_population);

        Buildings = new BuildingSystem(World, Citizens.Jobs, Civ);
        Citizens.OnJobDone = Buildings.OnJobCompleted;

        // 起步物资，够盖一座伐木场 + 一座农田
        Buildings.Stock.Wood = 40f;

        if (_renderer != null) _renderer.World = World;
        if (_buildingRenderer != null) _buildingRenderer.Buildings = Buildings;
        if (_citizenRenderer != null) _citizenRenderer.Citizens = Citizens;
        if (_inspector != null) _inspector.Citizens = Citizens;
        if (_buildTool != null) _buildTool.Buildings = Buildings;
        if (_camera != null) _camera.CenterOnWorld();
    }

    /// <summary>调试用：直接放一座完工的建筑。</summary>
    public void DebugPlace(BuildingType type, int tx, int ty)
    {
        int idx = Buildings.Place(tx, ty, type);
        if (idx >= 0)
            Buildings.OnJobCompleted(tx, ty, JobType.Build);
    }

    /// <summary>在目标点附近找一个能放的位置，直接建成。</summary>
    private bool TryPlaceNear(BuildingType type, int tx, int ty)
    {
        for (int r = 0; r <= 8; r++)
        {
            for (int dy = -r; dy <= r; dy++)
            {
                for (int dx = -r; dx <= r; dx++)
                {
                    if (Mathf.Abs(dx) != r && Mathf.Abs(dy) != r) continue;
                    int x = tx + dx, y = ty + dy;
                    if (!Buildings.CanPlace(x, y, type)) continue;
                    DebugPlace(type, x, y);
                    return true;
                }
            }
        }
        return false;
    }

    // ---------- 存档 ----------

    public bool SaveGame()
    {
        try
        {
            var data = World.ToSave();
            data.Tick = Clock.Tick;
            data.Language = Locale.Current;
            data.SavedAtUnix = System.DateTimeOffset.UtcNow.ToUnixTimeSeconds();

            string path = ProjectSettings.GlobalizePath(SavePath);
            System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path)!);
            string json = System.Text.Json.JsonSerializer.Serialize(data);
            System.IO.File.WriteAllText(path, json);
            GD.Print($"[Edict] 已存档 {json.Length} 字节 -> {path}");
            return true;
        }
        catch (System.Exception e)
        {
            GD.PushError($"[Edict] 存档失败: {e.Message}");
            return false;
        }
    }

    public bool LoadGame()
    {
        try
        {
            string path = ProjectSettings.GlobalizePath(SavePath);
            if (!System.IO.File.Exists(path))
            {
                GD.PushWarning("[Edict] 没有找到存档");
                return false;
            }

            string json = System.IO.File.ReadAllText(path);
            var data = System.Text.Json.JsonSerializer.Deserialize<SaveData>(json)
                       ?? throw new System.InvalidOperationException("存档为空");

            World = World.FromSave(data);
            Clock.Load(data.Tick);
            Locale.SetLanguage(data.Language);

            // TODO(M2)：市民与建筑状态暂不入档，读档后重新生成。
            Citizens = new CitizenSystem(World, World.Seed);
            Citizens.Spawn(_population);
            Buildings = new BuildingSystem(World, Citizens.Jobs, Civ);
            Citizens.OnJobDone = Buildings.OnJobCompleted;
            Buildings.Stock.Wood = 40f;

            _renderer.World = World;
            _buildingRenderer.Buildings = Buildings;
            _citizenRenderer.Citizens = Citizens;
            _inspector.Citizens = Citizens;
            _buildTool.Buildings = Buildings;
            _camera.World = World;
            _camera.CenterOnWorld();
            _hud.RebuildTexts();

            GD.Print($"[Edict] 已读档 tick={data.Tick}");
            return true;
        }
        catch (System.Exception e)
        {
            GD.PushError($"[Edict] 读档失败: {e.Message}");
            return false;
        }
    }
}
