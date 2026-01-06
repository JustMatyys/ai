from ollama import Client
import time
import os

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

client = Client()

def startup():
    global model
    clear()
    print("=======================================")
    print("Mathej2301 Python AI Chatbot, Hand-Made")
    print("=======================================")
    print("1. Minimax M2 (Cloud)")
    print("2. GPT-OSS 120b (Cloud)")
    print("3. DeepSeek-v3.1 671b (Cloud)")
    print("4. Qwen3-Coder 480b (Cloud)")
    print("""Type "exit" to exit.""")
    select = input("Co si přejete vybrat za model?: ")
    if select == "1":
        model = "minimax-m2:cloud"
    elif select == "2":
        model = "gpt-oss:120b-cloud"
    elif select == "3":
        model = "deepseek-v3.1:671b-cloud"
    elif select == "4":
        model = "qwen3-coder:480b-cloud"
    elif select == "exit":
        exit()
        
    elif select != "1" or "2" or "3" or "4":
        print("Vyber si prosím správný model!")
        time.sleep(3)
        print("\n" * 100)
        clear()
        startup()

startup()

while True:
    print("")
    content = input(">> ")
    
    if content.strip() == "exit":
        startup()
    
    messages = [
      {
        'role': 'user',
        'content': content,
      },
    ]

    for part in client.chat(model, messages=messages, stream=True):
      print(part['message']['content'], end='', flush=True)

      

