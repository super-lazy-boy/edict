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

    private TileRenderer _renderer = null!;
    private CitizenRenderer _citizenRenderer = null!;
    private CameraController _camera = null!;
    private InspectorPanel _inspector = null!;
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

        // 性能对照：--nopop 不生成市民，用于隔离渲染开销
        _population = OS.GetCmdlineUserArgs().Contains("--nopop") ? 0 : DefaultPopulation;
        NewWorld(DefaultSeed);

        _renderer = new TileRenderer { World = World };
        AddChild(_renderer);

        _citizenRenderer = new CitizenRenderer { Citizens = Citizens };
        AddChild(_citizenRenderer);

        _camera = new CameraController { World = World };
        AddChild(_camera);

        _inspector = new InspectorPanel { Citizens = Citizens, Renderer = _citizenRenderer };
        AddChild(_inspector);

        _hud = new Hud { Main = this };
        AddChild(_hud);

        GD.Print("[Edict] 启动完成");

        if (OS.GetCmdlineUserArgs().Contains("--shot"))
        {
            _shotFrames = 300;
            GD.Print("[Edict] 截图模式");
        }

        // 加速跑，用于验证市民能否完成工作
        if (OS.GetCmdlineUserArgs().Contains("--fast"))
        {
            Clock.Speed = 10.0;
            _shotFrames = 400;
            GD.Print("[Edict] 加速模式 10x");
        }

        _startTicks = Time.GetTicksMsec();
    }

    public override void _Process(double delta)
    {
        _frameCount++;

        int ticks = Clock.Advance(delta);
        for (int i = 0; i < ticks; i++)
            Citizens?.Tick((float)SimClock.TickSeconds);

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

        if (_renderer != null) _renderer.World = World;
        if (_citizenRenderer != null) _citizenRenderer.Citizens = Citizens;
        if (_inspector != null) _inspector.Citizens = Citizens;
        if (_camera != null) _camera.CenterOnWorld();
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

            // TODO(M1)：市民状态暂不入档，读档后重新生成。M2 补持久化。
            Citizens = new CitizenSystem(World, World.Seed);
            Citizens.Spawn(_population);

            _renderer.World = World;
            _citizenRenderer.Citizens = Citizens;
            _inspector.Citizens = Citizens;
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
