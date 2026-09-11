# API接口自动化测试项目

## 项目概述

基于 Python + Pytest + requests 对 JSONPlaceholder 公开 API 进行接口自动化测试，覆盖正常流程、异常入参、边界值场景共 15 条测试用例，使用 pytest-html 生成 HTML 测试报告。

## 技术栈

| 工具                   | 用途          |
| -------------------- | ----------- |
| Python 3.12          | 编程语言        |
| Pytest 9.0           | 测试框架        |
| requests             | HTTP 请求库    |
| pytest-html          | HTML 测试报告生成 |
| pytest-rerunfailures | 失败重试机制      |
| PyYAML               | 测试数据管理      |

## 项目结构

```
api_test_project/
├── common/                         # 核心框架层
│   └── base_api.py                # 基础API客户端封装（GET/POST/PUT/DELETE）
├── data/                           # 测试数据管理
│   └── posts_data.yaml            # 帖子模块测试数据（数据驱动）
├── reports/                        # 测试报告输出
│   └── report.html                # HTML 格式测试报告
├── testcases/                      # 测试用例目录
│   └── posts/
│       ├── posts_api.py           # 帖子API业务封装
│       └── test_posts.py          # 帖子测试用例（15条）
├── conftest.py                     # pytest 全局配置
├── pytest.ini                      # pytest 配置文件
├── requirements.txt                # 依赖清单
└── README.md
```

## 测试用例设计

### 正常流程（7条）

| 测试方法                              | 描述           | 期望状态码 |
| --------------------------------- | ------------ | ----- |
| test\_get\_post\_list             | 获取帖子列表       | 200   |
| test\_get\_post\_detail\[正常获取帖子1] | 获取帖子详情(ID=1) | 200   |
| test\_get\_post\_detail\[正常获取帖子2] | 获取帖子详情(ID=2) | 200   |
| test\_create\_post\[正常创建帖子]       | 创建新帖子        | 201   |
| test\_create\_post\[创建帖子-带特殊字符]   | 创建帖子(特殊字符)   | 201   |
| test\_update\_post                | 更新帖子         | 200   |
| test\_delete\_post                | 删除帖子         | 200   |

### 异常入参（5条）

| 测试方法                                 | 描述               | 期望状态码 |
| ------------------------------------ | ---------------- | ----- |
| test\_get\_post\_not\_found          | 获取不存在的帖子(ID=999) | 404   |
| test\_get\_post\_invalid\_id\_string | 非法字符ID("abc")    | 404   |
| test\_get\_post\_negative\_id        | 负数ID(-1)         | 404   |
| test\_create\_post\_missing\_title   | 创建帖子缺少title字段    | 201   |
| test\_update\_post\_not\_found       | 更新不存在的帖子(ID=999) | 500   |

### 边界值（3条）

| 测试方法                             | 描述               | 期望状态码 |
| -------------------------------- | ---------------- | ----- |
| test\_create\_post\_empty\_title | 空标题              | 201   |
| test\_create\_post\_empty\_body  | 空body            | 201   |
| test\_delete\_post\_not\_found   | 删除不存在的帖子(ID=999) | 200   |

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Youknowwho666/api-automation-test.git
cd api-automation-test
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行测试

```bash
# 运行所有测试
python -m pytest -v

# 运行并生成HTML报告
python -m pytest --html=reports/report.html --self-contained-html -v

# 失败重试（网络不稳定时使用）
python -m pytest --reruns 3 --reruns-delay 5 -v
```

### 5. 查看报告

打开 `reports/report.html` 查看测试结果。

## 分层架构设计

```
测试用例层 (test_posts.py)
    ↓ 调用
业务API层 (posts_api.py)
    ↓ 继承
基础API层 (base_api.py)
    ↓ 发送
JSONPlaceholder API
```

- **基础API层**：封装通用 HTTP 请求方法，支持 GET/POST/PUT/DELETE，统一超时和异常处理

- **业务API层**：继承基础API，封装帖子模块的具体接口

- **测试用例层**：调用业务API，执行测试并断言结果

- **数据驱动**：测试数据与代码分离，通过 YAML 文件管理

## 测试策略

- **数据驱动测试**：使用 YAML 文件管理测试数据，参数化测试覆盖多场景

- **多维度断言**：状态码 + 业务数据双重校验

- **异常场景覆盖**：不存在的ID、非法字符、负数、缺失字段

- **边界值测试**：空字符串、空body

- **失败重试机制**：网络波动时自动重试，提升稳定性

## 被测 API

- **目标**：JSONPlaceholder（<https://jsonplaceholder.typicode.com）>

- **类型**：免费公开的 RESTful API，无需认证

- **资源**：/posts（帖子的 CRUD 操作）