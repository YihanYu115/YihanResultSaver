import os
import datetime
import inspect
import importlib.util
import ast
import sys
import shutil
import numpy as np

class Tee(type(sys.stdout)):
    """Tee class to redirect output to both stdout and a file."""
    def __init__(self, file):
        self.file = file
        self.stdout = sys.stdout  # Save the original stdout

    def write(self, data):
        self.file.write(data)  # Write to the file
        self.stdout.write(data)  # Write to the original stdout (terminal)

    def flush(self):
        self.file.flush()  # Ensure file is flushed
        self.stdout.flush()  # Ensure terminal is flushed


def YihanResultSaver(description):
    """
    装饰器，用于记录函数运行日志、保存返回值，并复制源代码
    """
    def wrapper(func):
        def inner(*args, **kwargs):
        # 获取函数名和时间戳以及函数根目录
            func_name = func.__name__
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            FunPath = inspect.getsourcefile(func)
            ROOT_DIR = os.path.dirname(FunPath)
            ROOT_DIR = os.path.join(ROOT_DIR, "Results")
            if not os.path.exists(ROOT_DIR):
                os.makedirs(ROOT_DIR)
            LOG_FILE = os.path.join(ROOT_DIR, "run_log.txt")

            
            # 创建运行结果保存目录
            run_dir = os.path.join(ROOT_DIR, f"{func_name}_{timestamp}")
            os.makedirs(run_dir)

            # 记录日志信息
            log_message = f"[{timestamp}] Function: {func_name}\n"+\
                            f"Arguments: {args} {kwargs}\n"+\
                            f"Saved in: {run_dir}\n"+\
                            f"description: {description}\n"
            with open(LOG_FILE, "a", encoding="utf-8") as log_file:
                log_file.write(log_message + "-" * 40 + "\n")

            # 保存函数的源代码到结果目录
            try:
                modules = get_imported_modules(FunPath)
                to_save = [FunPath]
                for module in modules:
                    ispublic, modulepath = is_public_module(module[0])
                    ispublic or to_save.append(modulepath)
                for file_path in to_save:
                    if os.path.exists(file_path):
                        file_name = os.path.basename(file_path)
                        target_path = os.path.join(run_dir, "source_code")
                        if not os.path.exists(target_path):
                            os.makedirs(target_path)
                        target_path = os.path.join(target_path, file_name)
                        shutil.copy2(file_path, target_path)
                    else:
                        print(f"文件 {file_path} 不存在，跳过。")
            except Exception as e:
                # 如果源代码获取失败，记录到日志中
                with open(LOG_FILE, "a", encoding="utf-8") as log_file:
                    log_file.write(f"Error saving source code for {func_name}: {e}\n")

            # 执行目标函数并保存返回值
            result = None
            output_file = os.path.join(run_dir, "stdout.txt")
            with open(output_file, "w", encoding="utf-8") as f_out:
                # 使用Tee类实现输出到终端和文件
                sys.stdout = Tee(f_out)

                try:
                    result = func(*args, **kwargs)
                    # 保存函数的返回值到文件
                    np.save(os.path.join(run_dir, "result.npy"), result, allow_pickle=True)
                except Exception as e:
                    # 如果目标函数抛出异常，记录异常信息
                    error_message = f"Error in function {func_name}: {e}\n"
                    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
                        log_file.write(error_message)
                    raise
                finally:
                    sys.stdout = sys.stdout.stdout

            return result
        return inner
    return wrapper


def is_public_module(module_name):
    """
    判断模块是否为公开模块（标准库或第三方库）
    :param module_name: 模块名
    :return: (是否为公开模块, 模块路径)
    """
    try:
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            module_path = spec.origin
            # 判断是否在 site-packages 或者标准库路径中
            if "site-packages" in module_path or module_path.startswith(sys.base_prefix):
                return True, module_path
            else:
                return False, module_path
        else:
            return True, "Built-in or dynamically loaded module"
    except ModuleNotFoundError:
        return False, "Module not found"
    
def get_imported_modules(file_path):
    """
    获取指定 Python 文件中导入的模块和它们的物理地址
    :param file_path: Python 文件路径
    :return: 导入模块的列表，每个元素是 (模块名, 文件地址)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} does not exist.")

    # 读取文件内容
    with open(file_path, "r", encoding="utf-8") as file:
        file_content = file.read()

    # 使用 AST 分析源代码
    tree = ast.parse(file_content)

    imported_modules = []
    for node in ast.walk(tree):
        # 处理 `import module`
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                imported_modules.append(module_name)

        # 处理 `from module import ...`
        elif isinstance(node, ast.ImportFrom):
            if node.module:  # 忽略相对导入
                imported_modules.append(node.module)

    # 查找模块的实际地址
    module_info = []
    for module_name in imported_modules:
        try:
            # 获取模块的规范信息
            spec = importlib.util.find_spec(module_name)
            if spec and spec.origin:
                module_info.append((module_name, spec.origin))
            else:
                module_info.append((module_name, "Built-in or cannot locate"))
        except ModuleNotFoundError:
            module_info.append((module_name, "Module not found"))

    return module_info
