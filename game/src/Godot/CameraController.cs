using Godot;
using Edict.Core;

namespace Edict;

/// <summary>
/// 相机：中键拖拽平移，滚轮缩放，WASD 平移。
/// </summary>
public partial class CameraController : Camera2D
{
    public World World { get; set; } = null!;

    private const float MinZoom = 0.5f;
    private const float MaxZoom = 4.0f;
    private const float PanSpeed = 900f;

    private bool _dragging;
    private Vector2 _dragAnchor;

    public override void _Ready()
    {
        MakeCurrent();
        CenterOnWorld();
    }

    public void CenterOnWorld()
    {
        if (World == null) return;
        Position = new Vector2(
            World.Width * TileRenderer.TileSize * 0.5f,
            World.Height * TileRenderer.TileSize * 0.5f);
        Zoom = new Vector2(1f, 1f);
    }

    public override void _Process(double delta)
    {
        Vector2 dir = Vector2.Zero;
        if (Input.IsKeyPressed(Key.W) || Input.IsKeyPressed(Key.Up)) dir.Y -= 1;
        if (Input.IsKeyPressed(Key.S) || Input.IsKeyPressed(Key.Down)) dir.Y += 1;
        if (Input.IsKeyPressed(Key.A) || Input.IsKeyPressed(Key.Left)) dir.X -= 1;
        if (Input.IsKeyPressed(Key.D) || Input.IsKeyPressed(Key.Right)) dir.X += 1;

        if (dir != Vector2.Zero)
            Position += dir.Normalized() * PanSpeed * (float)delta / Zoom.X;
    }

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event is InputEventMouseButton mb)
        {
            if (mb.ButtonIndex == MouseButton.Middle)
            {
                _dragging = mb.Pressed;
                _dragAnchor = mb.Position;
                return;
            }

            if (mb.Pressed && (mb.ButtonIndex == MouseButton.WheelUp || mb.ButtonIndex == MouseButton.WheelDown))
            {
                ZoomAt(mb.ButtonIndex == MouseButton.WheelUp ? 1.15f : 1f / 1.15f);
                return;
            }
        }

        if (@event is InputEventMouseMotion mm && _dragging)
        {
            Position -= mm.Relative / Zoom.X;
        }
    }

    private void ZoomAt(float factor)
    {
        Vector2 mouseBefore = GetGlobalMousePosition();
        float z = Mathf.Clamp(Zoom.X * factor, MinZoom, MaxZoom);
        Zoom = new Vector2(z, z);
        Vector2 mouseAfter = GetGlobalMousePosition();
        Position += mouseBefore - mouseAfter;
    }
}
