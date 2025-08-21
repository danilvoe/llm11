# Запрос на создание кода
# Когда создаст нужно сохранить его в файл
# После этого нужно написать тесты
# Сохранить в файл
# Запустить тесты
# Вывести результат

import ollama #qwen3-coder:30b
import json
import re
import os
from dotenv import load_dotenv
import docker

class BasicActionLLM:
    def __init__(self):
        self.model = ""
        self.conversation_history = []
        self.system_prompt = """
            1. ответай и рассуждай только на Русском языке.
            2. Отвечай только фактом, без "я думаю", "можно сказать" и других рассуждений.
            3. не придумывай
            4. Ты эксперт по Python, LLM и ollama 
        """
        self.finish_prompt = ""
        self.think_delete = False

    def add_to_context(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})

    def clear_context(self):
        self.conversation_history = []

    def get_llm_response(self, prompt: str, role='user'):
        final_response = False
        self.add_to_context(role, prompt)
        try:
            client = ollama.Client(host=os.getenv('HOST_PORT_OLLAMA'))
            response = client.chat(
                model=os.getenv('OLLAMA_MODEL'),
                messages=self.conversation_history,
                stream=False,                
            )
            return response
        except Exception as e:
            print(f"Ошибка при обращении к LLM: {str(e)}")
            return final_response, ""

    def clean_response(self, llm_response: str):
        return re.sub(r"<think>.*?</think>", "", llm_response, flags=re.DOTALL).strip()

    def get_gamedev_tz_info(self):
        self.add_to_context("system", self.system_prompt)
        print(f"Бот: Могу проверить файл на Python, введите название файла в проекте для проверки")
        while True:
            try:
                user_input = input("\nВы: ").strip()
                final, response = self.get_llm_response(user_input)
                if final:
                    result = DockerRun.run_file_python(response.get('file_name'))
                    print(f'Результат выполнения файла: {result}')
                    break
                print(f"Бот_ТЗ: {response.content}")
            except Exception as e:
                print(f"Произошла ошибка: {e}")


class CodeWriteCodeCheck():
    def __init__(self):
        self.ai = BasicActionLLM()
    
    def start_dialog(self):
        print('Генерирую конесколько классов и в них по 3-5 методов')
        promt = "создай несколько классов и в них по 3-5 методов на Python. классы должны быть связаны между собой и иметь некую полезную работу. код должен иметь метод main. Нужен только, код без объяснений"
        result = self.ai.get_llm_response(promt)
        code = re.sub(r'^```python\s*|\s*```$', '', result.message.content, flags=re.MULTILINE)
        with open("code.py", "w") as file:
            file.write(code)
        print('Формирую тесты для полученного кода')
        promt = 'покрой ее тестированием. не забудь импорты от классов кода который будет проверятся! код находится в файле (code.py) Убедись что все импорты правильно указаны!'
        result = self.ai.get_llm_response(promt)
        test_code = re.sub(r'^```python\s*|\s*```$', '', result.message.content, flags=re.MULTILINE)
        print('Получил тесты, записываю в файл')
        with open("test_code.py", "w") as file:
            file.write(test_code)
        print('Запускаю тесты')
        doc = DockerRun()
        result_run_text = doc.run_file_python("test_code.py")
        print(result_run_text)

class DockerRun(BasicActionLLM):
    def __init__(self):
        self.model = os.getenv('OLLAMA_MODEL')
        self.conversation_history = []

        self.sending_prompt = ""
        self.think_delete = True
            
    @staticmethod
    def run_file_python(file_path:str):
        project_folder = '/home/lifeteo/LLM/AI_Advent_2025/llm11/'
        folder = '/project/'
        client = docker.from_env()
        try:
            result = client.containers.run(
                image ='python:3',
                command =f'python "{folder + file_path}"',
                volumes={
                    project_folder: {
                        'bind': folder,
                        'mode': 'rw'  # или 'ro' для read-only
                    }
                },
                remove=True,
                stderr=True,
                stdout=True
            )
        except Exception as e:
            return f"Ошибка выполнения тестов: {e.stderr}"
        return result.decode('utf-8')


def main():
    bot_info = BasicActionLLM()
    if os.path.exists('.env'):
        load_dotenv('.env')
    dialog = CodeWriteCodeCheck()
    print(dialog.start_dialog())

if __name__ == "__main__":
    main()