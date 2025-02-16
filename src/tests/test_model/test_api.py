from openai import OpenAI
import time

def test_deepseek_api():
    # 初始化客户端
    client = OpenAI(
        base_url='https://tbnx.plus7.plus/v1',
        api_key='sk-pe4cZ9jRpBKRzZ2uq2v0FW13iJgaL49SBbagj8HvWcEauWUu',
        timeout=30.0  # 设置30秒超时
    )
    
    # 获取可用模型列表
    try:
        models = client.models.list()
        print("\n可用模型列表:")
        for model in models.data:
            print(f"- {model.id}")
            
        # 测试每个模型
        test_prompt = "你好，请用一句话介绍自己。"
        for model in models.data:
            print(f"\n测试模型: {model.id}")
            try:
                completion = client.chat.completions.create(
                    model=model.id,
                    messages=[
                        {"role": "user", "content": test_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=100
                )
                print(f"响应: {completion.choices[0].message.content}")
            except Exception as e:
                print(f"测试失败: {str(e)}")
                
    except Exception as e:
        print(f"获取模型列表失败: {str(e)}")
            
if __name__ == "__main__":
    print("开始API测试...")
    print("API基础URL:", 'https://tbnx.plus7.plus/v1')
    test_deepseek_api() 