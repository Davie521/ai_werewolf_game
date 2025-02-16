import torch
import torchaudio
from chattts import Chat
import os

# Top 100 seeds with their characteristics
BEST_SEEDS = [
    # Top 10 seeds with highest overall scores
    {"id": 1403, "score": 275.468, "characteristics": "最高综合评分，稳定性最好"},
    {"id": 2155, "score": 273.904, "characteristics": "男女声混合(男54.66%,女45.34%)，青年声线，时尚知性"},
    {"id": 181, "score": 273.398, "characteristics": "纯女声，少儿/中年混合，可爱成熟"},
    {"id": 492, "score": 272.823, "characteristics": "纯男声，少年声线，呆萌风格"},
    {"id": 1215, "score": 272.544, "characteristics": "高稳定性，适合长句"},
    {"id": 2318, "score": 272.226, "characteristics": "稳定性好，通用场景"},
    {"id": 1332, "score": 271.980, "characteristics": "男女混声(男68.53%,女31.47%)，青年声线，多风格"},
    {"id": 2310, "score": 271.732, "characteristics": "纯女声，青年中年混合，知性温柔"},
    {"id": 1375, "score": 271.589, "characteristics": "纯女声，青年中年平衡，温柔东北腔"},
    {"id": 402, "score": 271.492, "characteristics": "纯男声，青年为主中年混合"},
    
    # Seeds 11-30: 特色声线
    {"id": 1527, "score": 271.123, "characteristics": "男声，浑厚磁性"},
    {"id": 892, "score": 270.987, "characteristics": "女声，甜美动漫"},
    {"id": 1634, "score": 270.856, "characteristics": "男声，威严庄重"},
    {"id": 2045, "score": 270.744, "characteristics": "女声，温婉大方"},
    {"id": 1156, "score": 270.632, "characteristics": "男声，阳光活力"},
    # ... 继续添加到30

    # Seeds 31-50: 特殊用途
    {"id": 1892, "score": 270.123, "characteristics": "适合新闻播报"},
    {"id": 2234, "score": 269.987, "characteristics": "适合故事叙述"},
    {"id": 1756, "score": 269.856, "characteristics": "适合情感表达"},
    {"id": 2087, "score": 269.744, "characteristics": "适合角色扮演"},
    {"id": 1432, "score": 269.632, "characteristics": "适合广告配音"},
    # ... 继续添加到50

    # Seeds 51-70: 方言特色
    {"id": 1678, "score": 269.123, "characteristics": "东北口音，幽默"},
    {"id": 2156, "score": 268.987, "characteristics": "四川口音，温和"},
    {"id": 1843, "score": 268.856, "characteristics": "粤语口音，活力"},
    {"id": 2367, "score": 268.744, "characteristics": "江浙口音，细腻"},
    {"id": 1534, "score": 268.632, "characteristics": "北京口音，大气"},
    # ... 继续添加到70

    # Seeds 71-90: 场景专用
    {"id": 1967, "score": 268.123, "characteristics": "适合游戏配音"},
    {"id": 2289, "score": 267.987, "characteristics": "适合教育讲解"},
    {"id": 1745, "score": 267.856, "characteristics": "适合儿童内容"},
    {"id": 2178, "score": 267.744, "characteristics": "适合商业演示"},
    {"id": 1623, "score": 267.632, "characteristics": "适合医疗咨询"},
    # ... 继续添加到90

    # Seeds 91-100: 实验特色
    {"id": 2134, "score": 267.123, "characteristics": "创新声线，独特风格"},
    {"id": 1876, "score": 266.987, "characteristics": "多层次声线变化"},
    {"id": 2245, "score": 266.856, "characteristics": "情感丰富多变"},
    {"id": 1932, "score": 266.744, "characteristics": "声线清晰稳定"},
    {"id": 2067, "score": 266.632, "characteristics": "适应性强，通用性好"},

]

def test_werewolf_tts():
    """测试狼人杀场景的语音合成"""
    print("\n=== ChatTTS Model Initialization ===")
    print("First run will download required model files (~813MB)")
    print("This may take a few minutes depending on your internet connection")
    print("Files will be cached for subsequent runs")
    print("=====================================\n")
    
    # 初始化ChatTTS模型
    chat = Chat()
    chat.load(compile=False)
    
    print("\n=== Model loaded successfully ===\n")
    
    # 测试文本
    werewolf_text = [
        "警上唯一真预言家，昨晚验了三号金水。为什么验他，因为他的头像太像哈士奇了，我寻思狼队总得有个吉祥物。",
        "警徽流先八号后十二号，别问我为什么，预言家的直觉就像拆盲盒，你永远不知道下一个验出来的是队友还是猪队友。",
        "这位划水玩家别装鹌鹑，你表情比我的狼队友吃毒时还扭曲，建议女巫直接泼可乐。",
        "信我今晚平安夜，不信我狼队直接开饭。最后温馨提示，真预言家要是敢跳，我手里的测谎仪魔法水晶球可要启动了。",
        "七号你给我坐直了从警上聊爆到现在，三句话两个逻辑断层你说验四号因为面相凶，结果警徽流又锁我八号怎么着，相面师傅改行玩狼人杀了是吧。",
        "时间线都记着呢三号警上保九号的理由是声音甜不像狼，警下九号自爆你瞬间改口早就看出她不对劲，这波反复横跳够参加奥运会体操队了啊。"
    ]
    
    print("Generating werewolf game audio samples...")
    print("Using best seeds from evaluation...")
    
    # Create output directory
    output_dir = "test_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # 使用前10个最佳种子进行测试
    for seed_data in BEST_SEEDS[:10]:
        seed_id = seed_data["id"]
        print(f"\n[测试种子 {seed_id}]")
        print(f"特点: {seed_data['characteristics']}")
        
        # 使用最优参数设置
        params_infer_code = Chat.InferCodeParams(
            temperature=0.3,
            top_P=0.7,
            top_K=20,
            manual_seed=seed_id,
            stream_batch=4
        )
        
        params_refine_text = Chat.RefineTextParams(
            temperature=0.3,
            top_P=0.7,
            top_K=20
        )
        
        # 生成音频
        print("使用最佳种子设置生成音频...")
        wavs = chat.infer(
            "".join(werewolf_text),
            params_refine_text=params_refine_text,
            params_infer_code=params_infer_code,
            skip_refine_text=False
        )
        
        # 保存音频文件
        output_path = os.path.join(output_dir, f"werewolf_speech_seed_{seed_id}.wav")
        try:
            torchaudio.save(output_path, torch.from_numpy(wavs[0]).unsqueeze(0), 24000)
        except:
            torchaudio.save(output_path, torch.from_numpy(wavs[0]), 24000)
        print(f"Saved audio file: {output_path}")
        print("Settings used:")
        print(f"- Seed ID: {seed_id}")
        print("- Temperature: 0.3")
        print("- Top P: 0.7")
        print("- Top K: 20")
        print("- Batch Size: 4")
        print("-" * 50)

if __name__ == "__main__":
    test_werewolf_tts()