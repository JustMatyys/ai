from ollama import Client
import time
import os

client = Client()

system_defualt = ("""
    'You are a helpful assistant.'
    'If a user tells you the word "exit", Say: "Welcome back 😎".'"""
)

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

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
    print("Q/q. Exit")
    print("")
    print("""Type "defualt" to set the instructions for the AI in this session. """)
    print("""That means the AI wont remember it. (Coming Soon, hopefully)""")
    print("")
    select = input("What model do you want to chose?: ")
    if select == "1":
        model = "minimax-m2:cloud"
        clear()
    elif select == "2":
        model = "gpt-oss:120b-cloud"
    elif select == "3":
        model = "deepseek-v3.1:671b-cloud"
    elif select == "4":
        model = "qwen3-coder:480b-cloud"
    elif select == "default":
        setup_default()
        startup()
    elif select == "q" or "Q":
        exit()
        
    elif select != "1" or "2" or "3" or "4":
        print("Vyber si prosím správný model!")
        time.sleep(3)
        print("\n" * 100)
        clear()
        startup()

def setup_default():
    global system_defualt
    clear()
    system_defualt = input("Napis nove defualtni chovani AI pro tuhle session v techto zavorkach '': ")

startup()

while True:
    content = input(">> ")
    
    if content.strip() == "exit":
        startup()
    
    messages = [
      {
        'role': 'user',
        'content': content,
      },
      {
        'role': 'system',
        'content': "'" + system_defualt + "'"
      },
    ]

    try:
        for part in client.chat(model, messages=messages, stream=True):
            print(part['message']['content'], end='', flush=True)
        print("")
    except:
        print("You may need to login or pull the model:", model)
        print("Don't worry, these are cloud models and wont take up any space!")
        print(" ")
        print("To login, go to your shell and type: ollama signin")
        print("To pull the model, type: ollama pull", model)
        print("")
        print("To exit type: exit")
