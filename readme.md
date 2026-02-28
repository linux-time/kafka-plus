# Kafka Plus 🚀

**Next-Gen Kafka Management & Observability Platform.** 一款为 2026 年运维量身定制的轻量级、高性能 Kafka 管理与日志观测平台。

[![License](https://img.shields.io/badge/license-Apache%202-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![Vector](https://img.shields.io/badge/Powered%20by-Vector-yellow.svg)](https://vector.dev/)
[![VictoriaLogs](https://img.shields.io/badge/Storage-VictoriaLogs-blueviolet.svg)](https://victoriametrics.com/)

---

## 🌟 为什么选择 Kafka Plus?

在管理 Kafka 集群时，你是否厌倦了沉重的 Java 工具和无法搜索的历史消息？  
**Kafka Plus** 采用 Python 异步控制平面，结合 Vector 的极速数据流处理和 VictoriaLogs 的海量存储，为你提供：

* **⚡ 极简运维：** 告别复杂的命令行，可视化管理 Topic、分区及消费者组。
* **🔍 海量检索：** 即使是 TB 级的历史消息，也能通过 LogsQL 实现秒级全文检索。
* **📉 智能采样：** 内置按需采样（Sampling）算法，最高节省 90% 的存储空间。
* **📊 物理看板：** 深入 Broker 磁盘空间，实时分析 Topic 的物理存储布局。
* **🚀 零感部署：** 容器化一键拉起，无需繁琐的 JVM 调优。

---

## 🏗️ 系统架构 (Architecture)



1.  **Control Plane:** 基于 **Flask (Gevent)** 的异步后端，负责资源编排与 Admin 调度。
2.  **Data Plane:** 利用 **Vector** 实现从 Kafka 到存储的高性能无损传输（Native Rust 性能）。
3.  **Storage Engine:** **VictoriaLogs** 提供超高压缩比（最高 10x）的日志索引与查询。

---

## ✨ 核心功能 (Features)

### 1. 集群全景图
* 实时监控 Broker 节点健康状况。
* 可视化 Topic 分区分布与副本状态（ISR）。

### 2. 存储深度分析
* **Disk Usage Ranking:** 一键识别占用硬盘最高的 Topic。
* **TTL 建议：** 根据数据增长曲线，智能建议消息留存（Retention）策略。

### 3. 消息观测站
* **Live Tail:** 实时查看消息流，支持关键字过滤。
* **History Search:** 基于 VictoriaLogs 的历史消息回溯，毫秒级响应。

### 4. 自动化运维
* **Vector Orchestrator:** 自动生成并热加载数据抓取配置，按需开启索引。
* **Offset Manager:** 可视化重置消费者组 Offset，支持按时间点回拨。

---

## 🚀 快速开始 (Quick Start)

### 环境要求
* Docker & Docker Compose
* Python 3.10+
* Kafka Cluster (支持 KRaft 或 Zookeeper 模式)

### 一键部署

```bash
# 1. 克隆项目
git clone [https://github.com/your-username/kafka-plus.git](https://github.com/your-username/kafka-plus.git)
cd kafka-plus

# 2. 启动基础组件 (Kafka, Vector, VictoriaLogs)
docker-compose up -d

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 启动后端服务
python main.py