from setuptools import setup, find_packages

setup(
    name="YihanResultSaver",  # 库的名称
    version="0.1.0",  # 版本号
    description="A Python decorator for logging, saving results, and tracking function source code.",  # 简短描述
    long_description=open("README.md", encoding="utf-8").read(),  # 长描述
    long_description_content_type="markdown",  # 长描述的格式
    author="Yihan Yu",  # 作者
    author_email="yihan.yu@iphy.ac.cn",  # 作者邮箱
    url="https://github.com/YihanYu115/YihanResultSaver.git",  # 项目主页
    license="MIT",  # 许可证
    packages=find_packages(),  # 自动查找子包
    python_requires=">=3.6",  # 支持的 Python 版本
    install_requires=["numpy>=1.21.0"],  # 依赖的库列表
)