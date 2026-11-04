# 附录 A 术语表

| id | 中文 | English | 定义 | 首现章 |
| --- | --- | --- | --- | --- |
| C001 | 检索增强生成 | Retrieval-Augmented Generation | 先检索资料，再让模型基于资料回答 | ch01 |
| C002 | 相关性 | Relevance | 检索结果是否真的回答了用户问题 | ch02 |
| C003 | 相似度 | Similarity | 向量空间里的距离度量 | ch02 |
| C004 | 语义压缩 | Semantic Compression | 把文本压成向量时丢掉字面信息 | ch02 |
| C005 | 切分粒度 | Chunk Granularity | 一个检索块包含多少上下文 | ch03 |
| C006 | 边界切断 | Boundary Cut | 切分点落在语义单元中间 | ch03 |
| C007 | 倒数排名融合 | Reciprocal Rank Fusion | 只按排名融合多路检索结果 | ch04 |
| C008 | 重排 | Rerank | 对候选集再排一次序 | ch04 |
| C009 | 检索缺失 | Retrieval Miss | 正确证据没有进入候选集 | ch05 |
| C010 | 生成越界 | Generation Overreach | 证据在场，模型仍超出证据回答 | ch05 |
| C011 | 失效边界 | Failure Boundary | 机制不再成立的条件 | ch06 |
| C012 | 抽样偏差 | Sampling Bias | 评测集与真实问题分布之间的偏离 | ch07 |
| C013 | 长上下文 | Long Context | 把更长的输入一次装进模型，用它替代挑段落 | ch08 |
