# DeepSeek API 最小调用示例
代码练习，先照着官方文档跑通，再关掉文档重写

## 前置条件
- Python314
- DeepSeek API key 可以去deepseek开放平台获取

## 配置
1. 复制 `.env.example` 为 `.env`
2. 在 `.env` 里填入你的 key

## 运行
1. 创建并激活虚拟环境
2. 安装依赖
python -m pip install -r requirements.txt
3. 运行脚本
python sdk_call.py
python HTTP_call.py

## 项目说明
- `sdk_call.py` —— 用 openai SDK 调用
- `HTTP_call.py` —— 用 requests 手写 HTTP 调用
SDK版本相当于给HTTP版本封包 HTTP版本会展示更多底层的细节 所以要写两个版本

## 我踩的坑
1. 在全局环境运行正常 在虚拟环境会报错 是因为虚拟环境少一些包 安装好后问题就会解决
2. git报dubious ownership 是因为.git属主和管理员权限不一致，Git拒绝操作 只需要把当前文件目录添加进安全目录里问题就会解决
3. requirements.txt编码变成UTF-16 可能会导致报错 是因为我电脑自带的PowerShell版本是老版本 可以cmd执行命令解决