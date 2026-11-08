using Godot;
using System.Collections.Generic;

namespace Edict;

/// <summary>
/// 极简本地化。文本全部走 key，禁止在代码里写死中文或英文。
/// 数据文件：locale/strings.txt（CSV：key,en,zh_CN）
/// </summary>
public static class Locale
{
    private const string Path = "res://locale/strings.txt";

    private static readonly Dictionary<string, string> En = new();
    private static readonly Dictionary<string, string> Zh = new();

    public static string Current { get; private set; } = "zh_CN";

    public static void Load()
    {
        En.Clear();
        Zh.Clear();

        using var f = FileAccess.Open(Path, FileAccess.ModeFlags.Read);
        if (f == null)
        {
            GD.PushError($"[Locale] 无法打开 {Path}");
            return;
        }

        bool header = true;
        while (!f.EofReached())
        {
            string line = f.GetLine().Trim();
            if (line.Length == 0 || line.StartsWith("#")) continue;
            if (header) { header = false; continue; }

            string[] cols = line.Split(',');
            if (cols.Length < 3) continue;
            En[cols[0]] = cols[1];
            Zh[cols[0]] = cols[2];
        }

        GD.Print($"[Locale] 载入 {En.Count} 条文本");
    }

    public static void SetLanguage(string code)
    {
        Current = code == "en" ? "en" : "zh_CN";
    }

    public static void Toggle()
    {
        SetLanguage(Current == "zh_CN" ? "en" : "zh_CN");
    }

    public static string Tr(string key)
    {
        var table = Current == "en" ? En : Zh;
        return table.TryGetValue(key, out var v) ? v : key;
    }
}
