namespace Edict.Core;

public enum CivId : byte
{
    Jixia = 0,      // 稷下 —— 文治
    Wolfplain = 1,  // 狼原 —— 武威
    Tide = 2,       // 潮汐 —— 商道
    Bedrock = 3,    // 磐石 —— 营造
    Incense = 4,    // 香火 —— 信仰
    Assembly = 5,   // 众议 —— 共和
}

/// <summary>
/// 国风修正系数。全部是倍率，1.0 = 无修正。
/// 系统只读这张表，不写特例代码。
/// </summary>
public struct CivModifiers
{
    public float AdminCapacity;
    public float CivilEfficiency;
    public float MilitaryPower;
    public float FarmOutput;
    public float IndustryOutput;
    public float TradeIncome;
    public float BuildSpeed;
    public float UnrestGain;
    public float NobleLoyaltyDrift;
    public float BetrayalChance;
    public float SalaryCost;

    public static CivModifiers Neutral => new()
    {
        AdminCapacity = 1f,
        CivilEfficiency = 1f,
        MilitaryPower = 1f,
        FarmOutput = 1f,
        IndustryOutput = 1f,
        TradeIncome = 1f,
        BuildSpeed = 1f,
        UnrestGain = 1f,
        NobleLoyaltyDrift = 0f,
        BetrayalChance = 1f,
        SalaryCost = 1f,
    };
}

public sealed class CivDefinition
{
    public CivId Id;
    public string NameKey = "";
    public string TraitKey = "";
    public string DescKey = "";
    public CivModifiers Mods = CivModifiers.Neutral;

    private static readonly CivDefinition[] All = BuildTable();

    public static CivDefinition Get(CivId id) => All[(int)id];
    public static CivDefinition[] List() => All;

    private static CivDefinition[] BuildTable()
    {
        var neutral = CivModifiers.Neutral;

        var jixia = neutral;
        jixia.AdminCapacity = 1.15f;
        jixia.CivilEfficiency = 1.20f;
        jixia.NobleLoyaltyDrift = -0.10f;   // 武将忠诚缓慢下滑

        var wolf = neutral;
        wolf.MilitaryPower = 1.25f;
        wolf.FarmOutput = 0.85f;
        wolf.BetrayalChance = 1.20f;

        var tide = neutral;
        tide.TradeIncome = 1.40f;
        tide.IndustryOutput = 1.05f;
        tide.AdminCapacity = 1.00f;

        var rock = neutral;
        rock.BuildSpeed = 1.35f;
        rock.SalaryCost = 1.25f;
        rock.MilitaryPower = 1.05f;

        var incense = neutral;
        incense.UnrestGain = 0.60f;
        incense.IndustryOutput = 0.80f;

        var assembly = neutral;
        assembly.BetrayalChance = 0.50f;
        assembly.AdminCapacity = 0.80f;
        assembly.CivilEfficiency = 0.85f;

        return new[]
        {
            new CivDefinition { Id = CivId.Jixia,     NameKey = "CIV_JIXIA_NAME",     TraitKey = "CIV_JIXIA_TRAIT",     DescKey = "CIV_JIXIA_DESC",     Mods = jixia },
            new CivDefinition { Id = CivId.Wolfplain, NameKey = "CIV_WOLFPLAIN_NAME", TraitKey = "CIV_WOLFPLAIN_TRAIT", DescKey = "CIV_WOLFPLAIN_DESC", Mods = wolf },
            new CivDefinition { Id = CivId.Tide,      NameKey = "CIV_TIDE_NAME",      TraitKey = "CIV_TIDE_TRAIT",      DescKey = "CIV_TIDE_DESC",      Mods = tide },
            new CivDefinition { Id = CivId.Bedrock,   NameKey = "CIV_BEDROCK_NAME",   TraitKey = "CIV_BEDROCK_TRAIT",   DescKey = "CIV_BEDROCK_DESC",   Mods = rock },
            new CivDefinition { Id = CivId.Incense,   NameKey = "CIV_INCENSE_NAME",   TraitKey = "CIV_INCENSE_TRAIT",   DescKey = "CIV_INCENSE_DESC",   Mods = incense },
            new CivDefinition { Id = CivId.Assembly,  NameKey = "CIV_ASSEMBLY_NAME",  TraitKey = "CIV_ASSEMBLY_TRAIT",  DescKey = "CIV_ASSEMBLY_DESC",  Mods = assembly },
        };
    }
}
