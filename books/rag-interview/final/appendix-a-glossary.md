# 附录 A 术语表

| id | 中文 | English | 定义 | 首现章 |
| --- | --- | --- | --- | --- |
| C001 | 检索增强生成 | Retrieval-Augmented Generation | 先检索资料，再让模型基于资料回答 | ch01 |
| C002 | 切分 | Chunking | 把长文档切成可检索的小块 | ch02 |
| C003 | 切分粒度 | Chunk Granularity | 一个检索块包含多少上下文 | ch02 |
| C004 | 召回 | Recall | 正确内容是否出现在候选集里 | ch03 |
| C005 | 语义压缩 | Semantic Compression | 把文本压成向量时丢掉字面信息 | ch03 |
| C006 | 混合检索 | Hybrid Retrieval | 同时用向量与关键词两路检索 | ch04 |
| C007 | 倒数排名融合 | Reciprocal Rank Fusion | 只按排名融合多路检索结果 | ch04 |
| C008 | 重排 | Rerank | 对候选集再排一次序 | ch04 |
| C009 | 检索缺失 | Retrieval Miss | 正确证据没有进入候选集 | ch05 |
| C010 | 生成越界 | Generation Overreach | 证据在场，模型仍超出证据回答 | ch05 |
| C011 | 评测集 | Evaluation Set | 固定的一组问题与期望答案 | ch06 |
| C012 | 系统设计 | System Design | 在条件不全时先定约束与验收，再选组件 | ch07 |
| C013 | 复盘 | Retrospective | 回看一次失败，找出当时判断错在哪并留下规则 | ch08 |
